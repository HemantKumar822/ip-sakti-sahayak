"""Factory function for instantiating LLM provider clients."""

import logging
from typing import Any

from src.config import config
from src.pipeline.providers.base import BaseLLMClient
from src.pipeline.providers.gemini import GeminiProvider
from src.pipeline.providers.omniroute import OmniRouteProvider
from src.pipeline.providers.openrouter import OpenRouterProvider

logger = logging.getLogger("ip_sakti.pipeline.providers.factory")


def get_llm_client(
    provider_name: str | None = None,
    **kwargs: Any,
) -> BaseLLMClient:
    """Instantiates and returns an LLM provider client conforming to BaseLLMClient.

    Args:
        provider_name: Optional provider identifier ('gemini', 'openrouter', or 'omniroute').
                       Defaults to config.LLM_PROVIDER.
        **kwargs: Provider-specific configuration overrides (api_key, model_name, etc.).

    Returns:
        An instance of BaseLLMClient.

    Raises:
        ValueError: If provider_name is not supported.
    """
    resolved_provider = (
        provider_name if provider_name is not None else config.LLM_PROVIDER
    )
    resolved_provider = resolved_provider.strip().lower()

    if resolved_provider == "gemini":
        return GeminiProvider(**kwargs)
    elif resolved_provider == "openrouter":
        return OpenRouterProvider(**kwargs)
    elif resolved_provider == "omniroute":
        return OmniRouteProvider(**kwargs)
    else:
        raise ValueError(
            f"Unsupported LLM provider: '{resolved_provider}'. Supported providers are: 'gemini', 'openrouter', 'omniroute'."
        )
