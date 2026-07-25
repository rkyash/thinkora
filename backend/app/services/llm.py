from typing import Any, AsyncGenerator, Dict, List, Optional, Tuple

import litellm

from app.config import settings

# Configure litellm to use environment variables for api keys
# e.g. OPENAI_API_KEY, ANTHROPIC_API_KEY, etc.


class LLMService:
    def __init__(self):
        # Enable LiteLLM's internal telemetry/logging if needed
        # litellm.set_verbose = False
        pass

    def _get_active_model(self) -> str:
        """
        Resolve the active LLM model string for the current provider.

        Falls back to ``settings.DEFAULT_MODEL`` when the provider-specific
        model attribute is empty, blank, or missing.
        """
        provider_map = {
            "openai": "OPENAI_MODEL",
            "anthropic": "ANTHROPIC_MODEL",
            "gemini": "GEMINI_MODEL",
            "groq": "GROQ_MODEL",
            "mistral": "MISTRAL_MODEL",
            "openrouter": "OPENROUTER_MODEL",
            "ollama": "OLLAMA_MODEL",
            "openai_proxy": "OPENAI_PROXY_MODEL",
        }
        attr = provider_map.get(settings.ACTIVE_PROVIDER)
        if attr:
            value = getattr(settings, attr, None)
            if value and value.strip():
                return value
        return settings.DEFAULT_MODEL

    def _inject_kwargs_for_model(self, model: str, kwargs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse provider from model prefix, read keys/URLs from settings,
        and inject them explicitly so LiteLLM doesn't rely on os.environ.
        """
        prefix = model.split("/")[0] if "/" in model else None
        
        prefix_map = {
            "openai": ("OPENAI_API_KEY", None),
            "anthropic": ("ANTHROPIC_API_KEY", None),
            "gemini": ("GEMINI_API_KEY", None),
            "groq": ("GROQ_API_KEY", None),
            "mistral": ("MISTRAL_API_KEY", None),
            "openrouter": ("OPENROUTER_API_KEY", None),
            "ollama": (None, "OLLAMA_BASE_URL"),
        }
        
        # Special handling for openai_proxy which shares the 'openai/' prefix
        if settings.ACTIVE_PROVIDER == "openai_proxy" and prefix == "openai":
            key_attr = "OPENAI_PROXY_API_KEY"
            base_url_attr = "OPENAI_PROXY_BASE_URL"
        else:
            info = prefix_map.get(prefix)
            if not info:
                return kwargs
            key_attr, base_url_attr = info
            
        if key_attr and getattr(settings, key_attr, None) and "api_key" not in kwargs:
            kwargs["api_key"] = getattr(settings, key_attr)
            
        if base_url_attr and getattr(settings, base_url_attr, None) and "api_base" not in kwargs:
            kwargs["api_base"] = getattr(settings, base_url_attr)
            
        return kwargs

    async def get_chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.7,
        **kwargs: Any,
    ) -> str:
        """
        Get a single non-streaming chat completion.
        """
        target_model = (model.strip() if model else None) or self._get_active_model()
        if not target_model or not target_model.strip():
            raise ValueError(
                "No LLM model configured. Please set a model in Settings → AI Provider."
            )
        kwargs = self._inject_kwargs_for_model(target_model, kwargs)

        response = await litellm.acompletion(
            model=target_model,
            messages=messages,
            temperature=temperature,
            **kwargs,
        )
        return response.choices[0].message.content

    async def get_chat_stream(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.7,
        **kwargs: Any,
    ) -> AsyncGenerator[str, None]:
        """
        Get a streaming chat completion.

        Yields text content chunks as they arrive.  For reasoning/thinking models
        (e.g. NVIDIA Nemotron with enable_thinking=True) the reasoning_content
        tokens are also yielded so the caller receives the full response.
        """
        target_model = (model.strip() if model else None) or self._get_active_model()
        if not target_model or not target_model.strip():
            raise ValueError(
                "No LLM model configured. Please set a model in Settings → AI Provider."
            )
        kwargs = self._inject_kwargs_for_model(target_model, kwargs)

        response = await litellm.acompletion(
            model=target_model,
            messages=messages,
            temperature=temperature,
            stream=True,
            **kwargs,
        )
        async for chunk in response:
            if not chunk.choices:
                continue
            delta = chunk.choices[0].delta
            # Skip reasoning/thinking tokens (e.g. Nemotron with enable_thinking).
            # These are the model's internal chain-of-thought and should NOT be
            # sent to the user — only the final content tokens matter.
            if delta.content is not None:
                yield delta.content

    async def get_embedding(
        self, text: str, model: Optional[str] = None, **kwargs: Any
    ) -> List[float]:
        """
        Get the embedding vector for a piece of text.
        """
        target_model = model or settings.EMBEDDING_MODEL
        kwargs = self._inject_kwargs_for_model(target_model, kwargs)

        response = await litellm.aembedding(
            model=target_model,
            input=[text],
            **kwargs,
        )
        return response.data[0]["embedding"]


# Singleton instance
llm_service = LLMService()


def get_llm_service() -> LLMService:
    return llm_service
