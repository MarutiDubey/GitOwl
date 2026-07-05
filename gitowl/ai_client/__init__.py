"""Provider-agnostic AI layer.

Every provider implements `AIProvider.review(diff, findings) -> ReviewResult`.
Use `get_provider(config)` (from `registry`) to obtain a configured instance.
"""

from gitowl.ai_client.base import AIProvider, AIProviderError
from gitowl.ai_client.registry import get_provider, register_provider

__all__ = [
    "AIProvider",
    "AIProviderError",
    "get_provider",
    "register_provider",
]
