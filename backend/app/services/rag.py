import json
import re
from typing import Any, AsyncGenerator, Dict, List

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import logger
from app.core.prompt_security import sanitize_user_content
from app.repositories.chunk import ChunkRepo
from app.services.llm import get_llm_service
from app.services.vector_store import get_vector_store

# ─── Greeting detection ────────────────────────────────────────────────────────

_GREETING_RE = re.compile(
    r'^\s*('
    r'hi+[!?.]*|hello+[!?.]*|hey+[!?.]*|howdy[!?.]*|'
    r'good\s*(morning|afternoon|evening|day|night)[!?.]*|'
    r'how\s+are\s+you[!?.]*|how\s+do\s+you\s+do[!?.]*|'
    r'what\s+\'?s\s+up[!?.]*|sup[!?.]*|greetings[!?.]*|'
    r'yo+[!?.]*|namaste[!?.]*|salut[!?.]*|'
    r'(nice|great|good|cool)\s+to\s+(meet|see)\s+you[!?.]*'
    r')\s*$',
    re.IGNORECASE,
)

def _is_greeting(text: str) -> bool:
    """Return True if the text is purely a casual greeting with no real question."""
    return bool(_GREETING_RE.match(text.strip()))

class RAGService:
    def __init__(self, db: AsyncSession):
        self._db = db
        self._llm = get_llm_service()
        self._vector_store = get_vector_store()
        self._chunk_repo = ChunkRepo()

    async def get_context(self, notebook_id: str, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Embed query, search Qdrant, and fetch full chunk text from Postgres.
        Returns a list of dicts with chunk context and metadata.
        """
        # 1. Embed query
        # We need to run it in a threadpool since it's blocking
        import asyncio

        from app.services.embedding import get_embedding_service
        
        embed_svc = get_embedding_service()
        query_vector = await asyncio.to_thread(embed_svc.embed_query, query)
        
        # 2. Search Qdrant
        results = await self._vector_store.search(notebook_id, query_vector, limit=top_k)
        if not results:
            return []

        qdrant_ids = [res["id"] for res in results]

        # 3. Fetch chunks from Postgres
        chunks = await self._chunk_repo.get_by_qdrant_ids(self._db, qdrant_ids)
        
        # 4. Map back to maintain ordering and scores
        chunk_map = {str(c.qdrant_point_id): c for c in chunks}
        
        context = []
        for res in results:
            chunk = chunk_map.get(res["id"])
            if chunk:
                context.append({
                    "content": chunk.content,
                    "source_id": str(chunk.source_id),
                    "score": res["score"],
                })
        
        return context

    async def stream_chat(
        self,
        notebook_id: str,
        messages: List[Dict[str, str]],
        model: str | None = None,
    ) -> AsyncGenerator[str, None]:
        """
        Perform RAG and stream the chat completion response.
        Yields JSON-encoded strings carrying content chunks, citations, or errors.
        """
        # Get the latest user message
        if not messages or messages[-1]["role"] != "user":
            yield json.dumps({"type": "error", "data": "Last message must be from user."})
            return

        query = messages[-1]["content"]
        # Sanitize the user query before using it in vector search or prompts (TASK-204)
        query = sanitize_user_content(query, max_chars=2_000)

        # ── Greeting fast-path: skip RAG, respond conversationally ────────────
        if _is_greeting(query):
            yield json.dumps({"type": "citations", "data": []}) + "\n"
            greeting_system = (
                "You are Thinkora, a friendly AI study assistant. "
                "The user has greeted you. Respond warmly and briefly (2-3 sentences). "
                "Then ask what topic or question they'd like to explore from their notebook. "
                "End your reply with a section:\n"
                "## Suggested Questions\n"
                "- (suggest 3-4 interesting study questions a student might ask about a notebook's content, "
                "using general academic examples since you don't know the specific notebook yet)"
            )
            greeting_messages = [{"role": "system", "content": greeting_system}] + messages
            try:
                async for chunk in self._llm.get_chat_stream(messages=greeting_messages, model=model):
                    yield json.dumps({"type": "chunk", "data": chunk}) + "\n"
            except Exception as e:
                logger.error("greeting_stream_error", error=str(e), exc_info=True)
                yield json.dumps({"type": "error", "data": str(e)}) + "\n"
            return

        # Get context
        contexts = await self.get_context(notebook_id, query)

        # Fetch source names for citation enrichment
        source_ids = list({ctx["source_id"] for ctx in contexts})
        source_name_map: Dict[str, str] = {}
        if source_ids:
            from app.repositories.source import SourceRepo
            source_repo = SourceRepo()
            for sid in source_ids:
                try:
                    src = await source_repo.get(self._db, sid)
                    if src:
                        source_name_map[sid] = src.name
                except Exception:
                    pass

        context_text = ""
        citations = []
        for idx, ctx in enumerate(contexts):
            # Sanitize source chunk text before embedding in system prompt (TASK-204)
            safe_content = sanitize_user_content(ctx['content'], max_chars=8_000)
            context_text += f"\n--- Source {idx+1} ---\n{safe_content}\n"
            citations.append({
                "source_id": ctx["source_id"],
                "score": ctx["score"],
                "name": source_name_map.get(ctx["source_id"], ""),
            })

        # Yield citations first (as a special event)
        yield json.dumps({"type": "citations", "data": citations}) + "\n"

        # Build prompt
        system_prompt = (
            "You are Thinkora, an expert AI tutor and knowledge assistant. "
            "Your mission is to deliver accurate, well-structured answers grounded strictly in the provided context.\n\n"

            "## How to Reason Before Answering\n"
            "1. Identify the user's **core intent** (concept explanation, comparison, step-by-step guide, code help, etc.).\n"
            "2. Scan the context for directly relevant information.\n"
            "3. Choose the response format that best serves the intent (see formatting rules below).\n"
            "4. If the context does not contain enough information, say so explicitly — never fabricate or guess.\n\n"

            "## Formatting Rules (ALWAYS follow these)\n\n"

            "### General Structure\n"
            "- Start with a concise **one-sentence direct answer** (no preamble like 'Great question!').\n"
            "- **NEVER repeat or quote back the user's question** in your answer — jump directly to the answer.\n"
            "- Use `## Section Title` headings to separate logical parts of a longer answer.\n"
            "- Keep simple questions short (2–5 sentences); expand only when complexity demands it.\n"
            "- For **long responses**, end with a `## Key Takeaways` section or a `> **📝 Summary:**` blockquote.\n\n"

            "### Lists — CRITICAL RULES\n"
            "- ALWAYS place each list item on its **own new line**.\n"
            "- NEVER write list items inline or separated by `*` within a sentence.\n"
            "- Bullet lists: use `- item` or `* item` (one item per line).\n"
            "- Numbered / step-by-step: use `1.`, `2.`, `3.` (one step per line).\n"
            "- Leave a **blank line before the first list item** and after the last.\n\n"

            "### Code\n"
            "- Always wrap code in fenced blocks with the language tag, e.g.:\n"
            "  ```python\n"
            "  # your code here\n"
            "  ```\n"
            "- Provide a brief explanation **before** the code block (what it does) and **after** (key points / gotchas).\n"
            "- Code must be complete and runnable where possible.\n\n"

            "### Comparisons\n"
            "- Use a Markdown table for side-by-side comparisons:\n"
            "  | Feature | Option A | Option B |\n"
            "  |---------|----------|----------|\n"
            "  | ...     | ...      | ...      |\n\n"

            "### Callouts & Tips\n"
            "- Use blockquotes for tips, warnings, and important notes:\n"
            "  `> **💡 Tip:** ...`\n"
            "  `> **⚠️ Warning:** ...`\n"
            "  `> **📌 Note:** ...`\n\n"

            "### Emphasis\n"
            "- Use `**bold**` for key terms, critical points, and important values.\n"
            "- Use `_italic_` for definitions, introductions of new concepts, or light emphasis.\n\n"

            "## Tone & Accuracy\n"
            "- Be professional, helpful, and friendly — like a knowledgeable senior colleague.\n"
            "- **Never hallucinate.** If you are uncertain, say: "
            "'_This is not explicitly covered in the provided context, but based on general knowledge..._' "
            "and clearly separate it from context-grounded content.\n"
            "- If the answer is entirely absent from the context, respond with: "
            "'> **❌ Not found in context:** The provided sources do not contain information about [topic]. "
            "Please consult additional resources or upload relevant material.'\n\n"

            "---\n\n"
            f"## Context\n{context_text}"
        )

        # Prepend system prompt; history already excludes the current user turn
        # (chat.py strips it before calling here, then rag_messages appends it again)
        rag_messages = [{"role": "system", "content": system_prompt}] + messages[:-1] + [{"role": "user", "content": query}]

        # Stream response
        try:
            async for chunk in self._llm.get_chat_stream(messages=rag_messages, model=model):
                yield json.dumps({"type": "chunk", "data": chunk}) + "\n"
        except Exception as e:
            logger.error("rag_stream_error", error=str(e), exc_info=True)
            yield json.dumps({"type": "error", "data": str(e)}) + "\n"
