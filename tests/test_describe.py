"""Tests for the PR-description feature (prompt parse, render, body merge)."""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest

from devguard.ai_client import get_provider
from devguard.ai_client.base import AIProviderError
from devguard.ai_client.prompt import parse_describe_response
from devguard.config import AIConfig
from devguard.describe import (
    DESCRIBE_BEGIN,
    DESCRIBE_END,
    describe_diff,
    merge_into_body,
    render_description,
)
from devguard.models import PrDescription


def _cfg(provider: str = "openrouter", api_key: str | None = "k") -> AIConfig:
    return AIConfig(provider=provider, model="m", base_url=None, api_key=api_key)


def _mock_response(payload: dict) -> MagicMock:
    resp = MagicMock()
    resp.raise_for_status.return_value = None
    resp.json.return_value = {"choices": [{"message": {"content": json.dumps(payload)}}]}
    return resp


# --- prompt parsing ----------------------------------------------------------


def test_parse_describe_full() -> None:
    payload = {"title": "Add caching", "summary": "Speeds reads.", "changes": ["a", "b"]}
    desc = parse_describe_response(json.dumps(payload))
    assert desc.title == "Add caching"
    assert desc.summary == "Speeds reads."
    assert desc.changes == ["a", "b"]


def test_parse_describe_defaults_and_filters_changes() -> None:
    # Missing title/summary get defaults; non-string / blank changes are dropped.
    payload = {"changes": ["keep", "", 5, "  ", " trim "]}
    desc = parse_describe_response(json.dumps(payload))
    assert desc.title == "Update"
    assert desc.summary == "No summary provided."
    assert desc.changes == ["keep", "trim"]


def test_parse_describe_tolerates_prose_wrapped_json() -> None:
    raw = 'Here you go:\n{"title": "T", "summary": "S", "changes": []}\nThanks!'
    desc = parse_describe_response(raw)
    assert desc.title == "T"
    assert desc.changes == []


# --- rendering ---------------------------------------------------------------


def test_render_includes_title_summary_changes() -> None:
    body = render_description(PrDescription(title="T", summary="S", changes=["one", "two"]))
    assert "## T" in body
    assert "S" in body
    assert "### Changes" in body
    assert "- one" in body
    assert "- two" in body


def test_render_omits_changes_heading_when_empty() -> None:
    body = render_description(PrDescription(title="T", summary="S", changes=[]))
    assert "### Changes" not in body


# --- body merge --------------------------------------------------------------


def test_merge_into_empty_body_wraps_in_markers() -> None:
    merged = merge_into_body(None, "SECTION")
    assert merged == f"{DESCRIBE_BEGIN}\nSECTION\n{DESCRIBE_END}"


def test_merge_appends_below_existing_text() -> None:
    merged = merge_into_body("Author notes.", "SECTION")
    assert merged.startswith("Author notes.")
    assert DESCRIBE_BEGIN in merged and "SECTION" in merged


def test_merge_replaces_previous_block_in_place() -> None:
    first = merge_into_body("Author notes.", "OLD")
    second = merge_into_body(first, "NEW")
    assert "NEW" in second
    assert "OLD" not in second
    # Author's text survives, and only one marked block remains.
    assert second.count(DESCRIBE_BEGIN) == 1
    assert "Author notes." in second


# --- provider.describe -------------------------------------------------------


def test_provider_describe_parses_response() -> None:
    payload = {"title": "T", "summary": "S", "changes": ["x"]}
    with patch(
        "devguard.ai_client.openai_compatible.httpx.post", return_value=_mock_response(payload)
    ):
        desc = get_provider(_cfg()).describe("diff")
    assert desc.title == "T"
    assert desc.changes == ["x"]


def test_describe_requires_api_key() -> None:
    with pytest.raises(AIProviderError, match="requires an API key"):
        get_provider(_cfg(api_key=None)).describe("diff")


# --- orchestrator ------------------------------------------------------------


def test_describe_diff_delegates_to_provider(config) -> None:
    provider = MagicMock()
    provider.describe.return_value = PrDescription(title="T", summary="S", changes=[])
    with patch("devguard.describe.get_provider", return_value=provider):
        desc = describe_diff("some diff", config)
    provider.describe.assert_called_once_with("some diff")
    assert desc.title == "T"
