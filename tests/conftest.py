"""Shared pytest fixtures."""

from __future__ import annotations

from pathlib import Path

import pytest

from gitowl.config import AIConfig, Config

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def sample_diff() -> str:
    return (FIXTURES / "sample.diff").read_text(encoding="utf-8")


@pytest.fixture
def config() -> Config:
    """A config pointing at OpenRouter with a dummy key (no live calls in tests)."""
    return Config(
        ai=AIConfig(
            provider="openrouter",
            model="openai/gpt-4o-mini",
            base_url="https://openrouter.ai/api/v1",
            api_key="test-key",
        ),
        github_token="test-token",
        semgrep_timeout_seconds=60,
        max_diff_lines=2000,
        log_level="INFO",
    )
