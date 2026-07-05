"""Provider registry — maps ``AI_PROVIDER`` values to provider classes.

To add a provider: implement :class:`~gitowl.ai_client.base.AIProvider` and
call :func:`register_provider`, or add it to ``_BUILTIN`` below.
"""

from __future__ import annotations

from gitowl.ai_client.base import AIProvider
from gitowl.ai_client.ollama import OllamaProvider
from gitowl.ai_client.openai_compatible import OpenAIProvider, OpenRouterProvider
from gitowl.config import AIConfig, ConfigError

_REGISTRY: dict[str, type[AIProvider]] = {}


def register_provider(provider_cls: type[AIProvider]) -> type[AIProvider]:
    """Register a provider class under its ``name``. Usable as a decorator."""
    key = provider_cls.name.strip().lower()
    if not key:
        raise ValueError("Provider class must define a non-empty 'name'")
    _REGISTRY[key] = provider_cls
    return provider_cls


# Built-in providers.
for _cls in (OpenRouterProvider, OpenAIProvider, OllamaProvider):
    register_provider(_cls)


def available_providers() -> list[str]:
    """Return the sorted list of registered provider names."""
    return sorted(_REGISTRY)


def get_provider(config: AIConfig) -> AIProvider:
    """Instantiate the provider named by ``config.provider``."""
    key = config.provider.strip().lower()
    provider_cls = _REGISTRY.get(key)
    if provider_cls is None:
        raise ConfigError(
            f"Unknown AI_PROVIDER '{config.provider}'. "
            f"Available: {', '.join(available_providers())}"
        )
    return provider_cls(config)
