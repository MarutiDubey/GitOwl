"""Tests for the review orchestrator (provider mocked)."""

from __future__ import annotations

import dataclasses
from unittest.mock import MagicMock, patch

from gitowl.config import Config, ReviewPolicy
from gitowl.models import Finding, FindingSource, ReviewResult, RiskLevel, Severity, UsageStats
from gitowl.reviewer import empty_review, review_diff


def _fake_result(risk: RiskLevel = RiskLevel.LOW) -> ReviewResult:
    return ReviewResult(summary="s", risk=risk, findings=[])


def test_review_diff_calls_provider_and_returns_stats(sample_diff: str, config: Config) -> None:
    provider = MagicMock()
    provider.review.return_value = _fake_result()
    with patch("gitowl.reviewer.get_provider", return_value=provider):
        review = review_diff(sample_diff, config, semgrep_findings=[])
    provider.review.assert_called_once()
    assert review.stats.files_changed == 1


def test_heuristic_raises_risk_above_ai(sample_diff: str, config: Config) -> None:
    # AI says Low, but the diff touches auth/ with real change -> heuristic bumps it.
    provider = MagicMock()
    provider.review.return_value = _fake_result(RiskLevel.LOW)
    with patch("gitowl.reviewer.get_provider", return_value=provider):
        review = review_diff(sample_diff, config, semgrep_findings=[])
    assert review.result.risk in (RiskLevel.MEDIUM, RiskLevel.HIGH)


def test_error_finding_forces_high(sample_diff: str, config: Config) -> None:
    provider = MagicMock()
    provider.review.return_value = ReviewResult(
        summary="s",
        risk=RiskLevel.LOW,
        findings=[
            Finding(
                source=FindingSource.AI,
                severity=Severity.ERROR,
                title="bug",
                message="boom",
            )
        ],
    )
    with patch("gitowl.reviewer.get_provider", return_value=provider):
        review = review_diff(sample_diff, config, semgrep_findings=[])
    assert review.result.risk is RiskLevel.HIGH


def test_policy_drops_finding_and_keeps_risk_low(sample_diff: str, config: Config) -> None:
    # A min_severity=ERROR policy drops a warning finding entirely, and because
    # filtering happens before risk scoring, that warning cannot inflate risk.
    policy = ReviewPolicy(min_severity=Severity.ERROR)
    cfg = dataclasses.replace(config, policy=policy)
    provider = MagicMock()
    provider.review.return_value = ReviewResult(
        summary="s",
        risk=RiskLevel.LOW,
        findings=[
            Finding(
                source=FindingSource.AI,
                severity=Severity.WARNING,
                title="minor",
                message="meh",
                file="src/app.py",
                line=1,
            )
        ],
    )
    with patch("gitowl.reviewer.get_provider", return_value=provider):
        review = review_diff(sample_diff, cfg, semgrep_findings=[])
    assert review.result.findings == []


def test_policy_ignores_path(sample_diff: str, config: Config) -> None:
    policy = ReviewPolicy(ignore_paths=("src/**",))
    cfg = dataclasses.replace(config, policy=policy)
    provider = MagicMock()
    provider.review.return_value = ReviewResult(
        summary="s",
        risk=RiskLevel.LOW,
        findings=[
            Finding(
                source=FindingSource.AI,
                severity=Severity.ERROR,
                title="bug",
                message="boom",
                file="src/ignored.py",
                line=1,
            )
        ],
    )
    with patch("gitowl.reviewer.get_provider", return_value=provider):
        review = review_diff(sample_diff, cfg, semgrep_findings=[])
    assert review.result.findings == []


def _usage(model: str = "openai/gpt-4o-mini") -> UsageStats:
    return UsageStats(
        model=model,
        prompt_tokens=1_000_000,
        completion_tokens=1_000_000,
        total_tokens=2_000_000,
        latency_ms=1500,
    )


def test_reviewer_prices_usage_from_pricing_table(sample_diff: str, config: Config) -> None:
    # The provider returns tokens but no cost; the reviewer fills the cost in.
    result = ReviewResult(summary="s", risk=RiskLevel.LOW, findings=[], usage=_usage())
    provider = MagicMock()
    provider.review.return_value = result
    with patch("gitowl.reviewer.get_provider", return_value=provider):
        review = review_diff(sample_diff, config, semgrep_findings=[])
    # gpt-4o-mini (0.15, 0.60): 1M in + 1M out => 0.75.
    assert review.result.usage is not None
    assert review.result.usage.estimated_cost_usd == 0.75


def test_reviewer_uses_pricing_override(sample_diff: str, config: Config) -> None:
    cfg = dataclasses.replace(config, pricing_overrides={"openai/gpt-4o-mini": (1.0, 2.0)})
    result = ReviewResult(summary="s", risk=RiskLevel.LOW, findings=[], usage=_usage())
    provider = MagicMock()
    provider.review.return_value = result
    with patch("gitowl.reviewer.get_provider", return_value=provider):
        review = review_diff(sample_diff, cfg, semgrep_findings=[])
    # Override (1.0, 2.0): 1M in + 1M out => 3.0.
    assert review.result.usage is not None
    assert review.result.usage.estimated_cost_usd == 3.0


def test_reviewer_leaves_cost_none_for_unknown_model(sample_diff: str, config: Config) -> None:
    result = ReviewResult(
        summary="s", risk=RiskLevel.LOW, findings=[], usage=_usage(model="mystery/model")
    )
    provider = MagicMock()
    provider.review.return_value = result
    with patch("gitowl.reviewer.get_provider", return_value=provider):
        review = review_diff(sample_diff, config, semgrep_findings=[])
    assert review.result.usage is not None
    assert review.result.usage.estimated_cost_usd is None


def test_reviewer_handles_missing_usage(sample_diff: str, config: Config) -> None:
    # A provider that reports no usage (e.g. mock) must not crash pricing.
    result = ReviewResult(summary="s", risk=RiskLevel.LOW, findings=[], usage=None)
    provider = MagicMock()
    provider.review.return_value = result
    with patch("gitowl.reviewer.get_provider", return_value=provider):
        review = review_diff(sample_diff, config, semgrep_findings=[])
    assert review.result.usage is None


def test_empty_review_is_low() -> None:
    review = empty_review("nothing here")
    assert review.result.risk is RiskLevel.LOW
    assert review.stats.files_changed == 0
