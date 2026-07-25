"""
Knowledge Graph Service — LangGraph-powered entity/relationship extraction.

Uses a two-node StateGraph:
  Node 1 (extract): LLM extracts entities and relationships as JSON.
  Node 2 (deduplicate): LLM merges duplicates and cleans the graph.

Persists GraphNode and GraphEdge records via repositories.
"""

from __future__ import annotations

import json
import math
import re
import random
from typing import Any, TypedDict

import structlog
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import GraphNodeType, MAX_GRAPH_NODES
from app.core.logging import logger
from app.models.graph_node import GraphNode
from app.models.graph_edge import GraphEdge
from app.repositories.chunk import ChunkRepo
from app.services.llm import get_llm_service
from app.core.prompt_security import sanitize_user_content

log: structlog.BoundLogger = structlog.get_logger(__name__)

chunk_repo = ChunkRepo()

# ─── LangGraph state ──────────────────────────────────────────────────────────

class GraphState(TypedDict):
    raw_text: str
    extracted: dict[str, Any]
    final: dict[str, Any]
    model: str | None


# ─── Graph Service ────────────────────────────────────────────────────────────

class GraphService:
    """
    Knowledge Graph extraction pipeline using a two-step LangGraph workflow.

    All LLM calls are routed through get_llm_service() — never call provider
    SDKs directly.
    """

    def __init__(self, db: AsyncSession) -> None:
        self._db = db
        self._llm = get_llm_service()

    # ─── Internal pipeline steps ─────────────────────────────────────────

    async def _extract_entities(self, state: GraphState) -> GraphState:
        """Node 1: Extract entities + relationships from raw text."""
        # Sanitize source text before embedding in LLM prompt (TASK-205)
        text_snippet = sanitize_user_content(state["raw_text"], max_chars=40_000)
        prompt = (
            "Extract entities and relationships from the text below.\n\n"
            "Return ONLY valid JSON (no markdown fences, no explanation):\n"
            '{\n'
            '  "nodes": [{"id": "unique_snake_case_id", "label": "Name", "type": "concept|entity|topic|person|place|event"}],\n'
            '  "edges": [{"source": "node_id1", "target": "node_id2", "label": "short verb phrase"}]\n'
            '}\n\n'
            "Rules:\n"
            f"- Maximum {MAX_GRAPH_NODES} nodes total.\n"
            "- Every edge must reference valid node ids from the nodes array.\n"
            '- Node ids are short snake_case strings (e.g. "machine_learning", "alan_turing").\n'
            "- Node labels are human-readable display names.\n"
            "- Edge labels are short verb phrases (\u2264 5 words) describing the relationship.\n"
            "- Skip trivial or very generic nodes.\n\n"
            f"Text:\n{text_snippet}"
        )
        messages = [{"role": "user", "content": prompt}]
        raw = await self._llm.get_chat_completion(
            messages=messages, model=state.get("model"), temperature=0.2
        )
        try:
            extracted = _extract_json(raw)
        except ValueError:
            log.warning("graph_extract_json_error", raw=raw[:300])
            extracted = {"nodes": [], "edges": []}
        state["extracted"] = extracted
        return state

    async def _deduplicate_entities(self, state: GraphState) -> GraphState:
        """Node 2: Merge duplicates and clean the graph."""
        if not state.get("extracted", {}).get("nodes"):
            state["final"] = {"nodes": [], "edges": []}
            return state

        graph_json = json.dumps(state["extracted"], indent=2)
        # Build prompt inline (avoids .format() conflicts with JSON braces in schema example)
        prompt = (
            "You are given a knowledge graph with potentially duplicate nodes and edges.\n"
            "Merge duplicate concepts (same entity referred to by slightly different names).\n"
            "Remove self-loops and duplicate edges.\n\n"
            f"Input JSON:\n{graph_json}\n\n"
            "Return ONLY the cleaned graph as valid JSON (same schema as input, no markdown fences):\n"
            '{\n  "nodes": [...],\n  "edges": [...]\n}'
        )
        messages = [{"role": "user", "content": prompt}]
        raw = await self._llm.get_chat_completion(
            messages=messages, model=state.get("model"), temperature=0.1
        )
        try:
            final = _extract_json(raw)
        except ValueError:
            log.warning("graph_dedup_json_error", raw=raw[:300])
            final = state["extracted"]
        state["final"] = final
        return state

    # ─── Public API ───────────────────────────────────────────────────────

    async def get_graph(self, notebook_id: str) -> dict[str, list]:
        """Return all nodes + edges for a notebook."""
        node_result = await self._db.execute(
            select(GraphNode).where(GraphNode.notebook_id == notebook_id)
        )
        nodes = list(node_result.scalars().all())

        edge_result = await self._db.execute(
            select(GraphEdge).where(GraphEdge.notebook_id == notebook_id)
        )
        edges = list(edge_result.scalars().all())

        return {"nodes": nodes, "edges": edges}

    async def refresh_graph(
        self, notebook_id: str, model: str | None = None
    ) -> dict[str, list]:
        """
        Regenerate the knowledge graph for a notebook:
          1. Collect all chunk text.
          2. Run the two-node LangGraph pipeline.
          3. Delete existing nodes/edges for the notebook.
          4. Persist new nodes and edges.
          5. Return the new graph.
        """
        # Collect text
        chunks = await chunk_repo.list_all(self._db, notebook_id=notebook_id, limit=300)
        raw_text = "\n\n".join(c.content or "" for c in chunks)
        if not raw_text.strip():
            return {"nodes": [], "edges": []}

        log.info("graph_refresh_start", notebook_id=notebook_id)

        # Run pipeline (simple sequential without LangGraph dependency for now)
        state: GraphState = {
            "raw_text": raw_text,
            "extracted": {},
            "final": {},
            "model": model,
        }
        state = await self._extract_entities(state)
        state = await self._deduplicate_entities(state)

        final = state["final"]
        raw_nodes: list[dict] = final.get("nodes", [])
        raw_edges: list[dict] = final.get("edges", [])

        # Enforce node cap
        raw_nodes = raw_nodes[:MAX_GRAPH_NODES]
        valid_ids = {n["id"] for n in raw_nodes}

        # Delete existing graph data
        await self._db.execute(
            delete(GraphEdge).where(GraphEdge.notebook_id == notebook_id)
        )
        await self._db.execute(
            delete(GraphNode).where(GraphNode.notebook_id == notebook_id)
        )
        await self._db.flush()

        # Insert new nodes with layout positions (simple radial layout)
        n_count = len(raw_nodes)
        db_node_map: dict[str, GraphNode] = {}
        node_rows: list[GraphNode] = []
        for i, raw_node in enumerate(raw_nodes):
            angle = (2 * math.pi * i) / max(n_count, 1)
            radius = 350
            x = radius * math.cos(angle) + random.uniform(-20, 20)
            y = radius * math.sin(angle) + random.uniform(-20, 20)

            raw_type = raw_node.get("type", "concept").lower()
            try:
                node_type = GraphNodeType(raw_type)
            except ValueError:
                node_type = GraphNodeType.CONCEPT

            node = GraphNode(
                notebook_id=notebook_id,
                label=str(raw_node.get("label", raw_node.get("id", ""))),
                type=node_type,
                x_pos=round(x, 2),
                y_pos=round(y, 2),
            )
            self._db.add(node)
            node_rows.append(node)

        await self._db.flush()
        for i, raw_node in enumerate(raw_nodes):
            node_obj = node_rows[i]
            await self._db.refresh(node_obj)
            db_node_map[raw_node["id"]] = node_obj

        # Insert edges — only where both ends exist
        edge_rows: list[GraphEdge] = []
        seen_edges: set[tuple[str, str]] = set()
        for raw_edge in raw_edges:
            src_id = raw_edge.get("source", "")
            tgt_id = raw_edge.get("target", "")
            if src_id not in valid_ids or tgt_id not in valid_ids:
                continue
            if src_id == tgt_id:
                continue
            key = (src_id, tgt_id)
            if key in seen_edges:
                continue
            seen_edges.add(key)

            src_node = db_node_map.get(src_id)
            tgt_node = db_node_map.get(tgt_id)
            if not src_node or not tgt_node:
                continue

            edge = GraphEdge(
                notebook_id=notebook_id,
                source_node=str(src_node.id),
                target_node=str(tgt_node.id),
                label=str(raw_edge.get("label", ""))[:255],
            )
            self._db.add(edge)
            edge_rows.append(edge)

        await self._db.flush()
        for edge in edge_rows:
            await self._db.refresh(edge)

        log.info(
            "graph_refresh_done",
            notebook_id=notebook_id,
            nodes=len(node_rows),
            edges=len(edge_rows),
        )
        return {"nodes": node_rows, "edges": edge_rows}

    async def add_node(
        self,
        notebook_id: str,
        label: str,
        node_type: GraphNodeType = GraphNodeType.CONCEPT,
        x_pos: float = 0.0,
        y_pos: float = 0.0,
    ) -> GraphNode:
        """Manually add a node to the graph."""
        node = GraphNode(
            notebook_id=notebook_id,
            label=label,
            type=node_type,
            x_pos=x_pos,
            y_pos=y_pos,
        )
        self._db.add(node)
        await self._db.flush()
        await self._db.refresh(node)
        return node

    async def delete_node(self, node_id: str, notebook_id: str) -> bool:
        """Delete a node and all connected edges."""
        result = await self._db.execute(
            select(GraphNode).where(
                GraphNode.id == node_id,
                GraphNode.notebook_id == notebook_id,
            )
        )
        node = result.scalar_one_or_none()
        if node is None:
            return False

        # Delete connected edges first
        await self._db.execute(
            delete(GraphEdge).where(
                (GraphEdge.source_node == node_id) | (GraphEdge.target_node == node_id)
            )
        )
        await self._db.delete(node)
        await self._db.flush()
        return True


# ─── Helper ───────────────────────────────────────────────────────────────────

def _extract_json(text: str) -> Any:
    """Extract and parse the first JSON object or array from LLM output."""
    text = re.sub(r"```(?:json)?\s*", "", text)
    text = text.strip().rstrip("`").strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    match = re.search(r"(\{.*\}|\[.*\])", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass
    raise ValueError(f"Could not extract JSON from: {text[:200]}")
