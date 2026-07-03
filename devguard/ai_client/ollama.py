"""Ollama provider — local, free, OpenAI-compatible chat endpoint.

Ollama exposes an OpenAI-compatible API at ``/v1``, so it reuses the shared
base and simply requires no API key.
"""

from __future__ import annotations

from devguard.ai_client.openai_compatible import OpenAICompatibleProvider


class OllamaProvider(OpenAICompatibleProvider):
    """Talk to a local Ollama server (default provider for zero-cost dev)."""

    name = "ollama"
    default_base_url = "http://localhost:11434/v1"
    requires_api_key = False

    def _base_url(self) -> str:
        # Allow AI_BASE_URL=http://localhost:11434 (without /v1) and normalise.
        base = (self.config.base_url or self.default_base_url).rstrip("/")
        if not base.endswith("/v1"):
            base = f"{base}/v1"
        return base
