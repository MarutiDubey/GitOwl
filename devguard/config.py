"""Runtime configuration loaded from environment (.env)."""

from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv

# Load .env once at import time. Values already set in the real environment win.
load_dotenv(override=False)


class ConfigError(RuntimeError):
    """Raised when required configuration is missing or invalid."""


@dataclass(frozen=True)
class AIConfig:
    """Configuration for the AI provider layer."""

    provider: str
    model: str
    base_url: str | None
    api_key: str | None


@dataclass(frozen=True)
class Config:
    """Top-level DevGuard configuration."""

    ai: AIConfig
    github_token: str | None
    semgrep_timeout_seconds: int
    max_diff_lines: int
    log_level: str


def _get_int(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None or raw.strip() == "":
        return default
    try:
        return int(raw)
    except ValueError as exc:  # pragma: no cover - defensive
        raise ConfigError(f"{name} must be an integer, got {raw!r}") from exc


def load_config() -> Config:
    """Build a Config from the current environment."""
    provider = os.getenv("AI_PROVIDER", "openrouter").strip().lower()
    ai = AIConfig(
        provider=provider,
        model=os.getenv("AI_MODEL", "openai/gpt-4o-mini"),
        base_url=os.getenv("AI_BASE_URL") or None,
        api_key=os.getenv("AI_API_KEY") or None,
    )
    return Config(
        ai=ai,
        github_token=os.getenv("GITHUB_TOKEN") or None,
        semgrep_timeout_seconds=_get_int("SEMGREP_TIMEOUT_SECONDS", 60),
        max_diff_lines=_get_int("MAX_DIFF_LINES", 2000),
        log_level=os.getenv("LOG_LEVEL", "INFO"),
    )
