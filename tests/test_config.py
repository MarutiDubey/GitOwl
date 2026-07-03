"""Tests for environment-driven configuration."""

from __future__ import annotations

import pytest

from devguard.config import load_config


def test_defaults_to_openrouter(monkeypatch: pytest.MonkeyPatch) -> None:
    for key in ("AI_PROVIDER", "AI_MODEL", "AI_BASE_URL", "AI_API_KEY"):
        monkeypatch.delenv(key, raising=False)
    cfg = load_config()
    assert cfg.ai.provider == "openrouter"
    assert cfg.ai.model == "openai/gpt-4o-mini"


def test_env_overrides_provider(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AI_PROVIDER", "Ollama")
    monkeypatch.setenv("AI_MODEL", "llama3.1")
    cfg = load_config()
    assert cfg.ai.provider == "ollama"  # normalised to lowercase
    assert cfg.ai.model == "llama3.1"


def test_numeric_settings_parsed(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MAX_DIFF_LINES", "500")
    monkeypatch.setenv("SEMGREP_TIMEOUT_SECONDS", "30")
    cfg = load_config()
    assert cfg.max_diff_lines == 500
    assert cfg.semgrep_timeout_seconds == 30


def test_bad_int_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    from devguard.config import ConfigError

    monkeypatch.setenv("MAX_DIFF_LINES", "not-a-number")
    with pytest.raises(ConfigError):
        load_config()
