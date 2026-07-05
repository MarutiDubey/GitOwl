"""Tests for environment-driven configuration."""

from __future__ import annotations

from pathlib import Path

import pytest

from gitowl.config import ConfigError, ReviewPolicy, load_config
from gitowl.models import Severity


def _write_toml(tmp_path: Path, body: str) -> Path:
    path = tmp_path / ".gitowl.toml"
    path.write_text(body, encoding="utf-8")
    return path


def test_defaults_to_openrouter(monkeypatch: pytest.MonkeyPatch) -> None:
    for key in ("AI_PROVIDER", "AI_MODEL", "AI_BASE_URL", "AI_API_KEY"):
        monkeypatch.delenv(key, raising=False)
    cfg = load_config()
    assert cfg.ai.provider == "openrouter"
    assert cfg.ai.model == "openai/gpt-4o-mini"


def test_missing_toml_uses_default_policy(tmp_path: Path) -> None:
    # Point at a directory with no .gitowl.toml -> defaults, no error.
    cfg = load_config(config_path=tmp_path / ".gitowl.toml")
    assert cfg.policy == ReviewPolicy()
    assert cfg.policy.min_severity is Severity.INFO
    assert cfg.policy.ignore_paths == ()


def test_toml_review_policy_parsed(tmp_path: Path) -> None:
    path = _write_toml(
        tmp_path,
        '[review]\nmin_severity = "warning"\nignore_paths = ["tests/**", "*.md"]\n',
    )
    cfg = load_config(config_path=path)
    assert cfg.policy.min_severity is Severity.WARNING
    assert cfg.policy.ignore_paths == ("tests/**", "*.md")


def test_toml_ai_model_applied(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("AI_MODEL", raising=False)
    path = _write_toml(tmp_path, '[ai]\nmodel = "anthropic/claude-3.5"\n')
    cfg = load_config(config_path=path)
    assert cfg.ai.model == "anthropic/claude-3.5"


def test_env_model_overrides_toml(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    # Precedence proof: env wins over the toml file.
    monkeypatch.setenv("AI_MODEL", "env/model")
    path = _write_toml(tmp_path, '[ai]\nmodel = "toml/model"\n')
    cfg = load_config(config_path=path)
    assert cfg.ai.model == "env/model"


def test_malformed_toml_raises(tmp_path: Path) -> None:
    path = _write_toml(tmp_path, "this is = not valid toml [[[")
    with pytest.raises(ConfigError):
        load_config(config_path=path)


def test_bad_min_severity_raises(tmp_path: Path) -> None:
    path = _write_toml(tmp_path, '[review]\nmin_severity = "critical"\n')
    with pytest.raises(ConfigError):
        load_config(config_path=path)


def test_ignore_paths_must_be_string_list(tmp_path: Path) -> None:
    path = _write_toml(tmp_path, "[review]\nignore_paths = [1, 2]\n")
    with pytest.raises(ConfigError):
        load_config(config_path=path)


def test_pricing_override_parsed(tmp_path: Path) -> None:
    path = _write_toml(
        tmp_path,
        '[pricing]\n"openai/gpt-4o-mini" = [1.0, 2.0]\n"local/model" = [0, 0]\n',
    )
    cfg = load_config(config_path=path)
    assert cfg.pricing_overrides["openai/gpt-4o-mini"] == (1.0, 2.0)
    assert cfg.pricing_overrides["local/model"] == (0.0, 0.0)


def test_missing_pricing_is_empty(tmp_path: Path) -> None:
    cfg = load_config(config_path=tmp_path / ".gitowl.toml")
    assert cfg.pricing_overrides == {}


def test_bad_pricing_shape_raises(tmp_path: Path) -> None:
    # Three numbers instead of [input, output].
    path = _write_toml(tmp_path, '[pricing]\n"m" = [1, 2, 3]\n')
    with pytest.raises(ConfigError):
        load_config(config_path=path)


def test_pricing_non_numeric_raises(tmp_path: Path) -> None:
    path = _write_toml(tmp_path, '[pricing]\n"m" = ["a", "b"]\n')
    with pytest.raises(ConfigError):
        load_config(config_path=path)


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
    from gitowl.config import ConfigError

    monkeypatch.setenv("MAX_DIFF_LINES", "not-a-number")
    with pytest.raises(ConfigError):
        load_config()
