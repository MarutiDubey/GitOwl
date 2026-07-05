"""Tests for AI providers with the HTTP layer mocked — never hits a live API."""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import httpx
import pytest

from gitowl.ai_client import get_provider
from gitowl.ai_client.base import AIProviderError
from gitowl.ai_client.registry import available_providers
from gitowl.config import AIConfig, ConfigError
from gitowl.models import RiskLevel


def _cfg(provider: str = "openrouter", api_key: str | None = "k") -> AIConfig:
    return AIConfig(provider=provider, model="m", base_url=None, api_key=api_key)


def _mock_response(payload: dict, usage: dict | None = None) -> MagicMock:
    resp = MagicMock()
    resp.raise_for_status.return_value = None
    body: dict = {"choices": [{"message": {"content": json.dumps(payload)}}]}
    if usage is not None:
        body["usage"] = usage
    resp.json.return_value = body
    return resp


def test_registry_lists_builtin_providers() -> None:
    assert {"openrouter", "openai", "ollama"} <= set(available_providers())


def test_unknown_provider_raises() -> None:
    with pytest.raises(ConfigError):
        get_provider(_cfg(provider="does-not-exist"))


def test_openrouter_requires_api_key() -> None:
    provider = get_provider(_cfg(api_key=None))
    with pytest.raises(AIProviderError, match="requires an API key"):
        provider.review("diff", [])


def test_ollama_does_not_require_api_key() -> None:
    payload = {"summary": "ok", "risk": "Low", "findings": []}
    with patch(
        "gitowl.ai_client.openai_compatible.httpx.post", return_value=_mock_response(payload)
    ):
        provider = get_provider(_cfg(provider="ollama", api_key=None))
        result = provider.review("diff", [])
    assert result.risk is RiskLevel.LOW


def test_provider_parses_successful_response() -> None:
    payload = {
        "summary": "All good.",
        "risk": "High",
        "findings": [{"severity": "error", "title": "X", "message": "y"}],
    }
    with patch(
        "gitowl.ai_client.openai_compatible.httpx.post", return_value=_mock_response(payload)
    ):
        result = get_provider(_cfg()).review("diff", [])
    assert result.risk is RiskLevel.HIGH
    assert result.findings[0].title == "X"


def test_provider_captures_usage_tokens() -> None:
    payload = {"summary": "ok", "risk": "Low", "findings": []}
    usage = {"prompt_tokens": 800, "completion_tokens": 200, "total_tokens": 1000}
    with patch(
        "gitowl.ai_client.openai_compatible.httpx.post",
        return_value=_mock_response(payload, usage=usage),
    ):
        result = get_provider(_cfg()).review("diff", [])
    assert result.usage is not None
    assert result.usage.prompt_tokens == 800
    assert result.usage.completion_tokens == 200
    assert result.usage.total_tokens == 1000
    assert result.usage.model == "m"
    assert result.usage.latency_ms >= 0
    # The provider does not price the call; that's the reviewer's job.
    assert result.usage.estimated_cost_usd is None


def test_provider_usage_defaults_when_absent() -> None:
    # A response with no usage block still yields a UsageStats (zeroed tokens).
    payload = {"summary": "ok", "risk": "Low", "findings": []}
    with patch(
        "gitowl.ai_client.openai_compatible.httpx.post", return_value=_mock_response(payload)
    ):
        result = get_provider(_cfg()).review("diff", [])
    assert result.usage is not None
    assert result.usage.total_tokens == 0


def test_http_error_becomes_provider_error() -> None:
    err_resp = MagicMock()
    err_resp.status_code = 401
    err_resp.text = "unauthorized"
    exc = httpx.HTTPStatusError("401", request=MagicMock(), response=err_resp)
    failing = MagicMock()
    failing.raise_for_status.side_effect = exc
    with patch("gitowl.ai_client.openai_compatible.httpx.post", return_value=failing):
        with pytest.raises(AIProviderError, match="401"):
            get_provider(_cfg()).review("diff", [])


def test_openrouter_sends_attribution_headers() -> None:
    payload = {"summary": "ok", "risk": "Low", "findings": []}
    with patch(
        "gitowl.ai_client.openai_compatible.httpx.post", return_value=_mock_response(payload)
    ) as post:
        get_provider(_cfg()).review("diff", [])
    headers = post.call_args.kwargs["headers"]
    assert headers["Authorization"] == "Bearer k"
    assert "X-Title" in headers
