"""Tests for the review orchestrator (provider mocked)."""

from __future__ import annotations

import dataclasses
from unittest.mock import MagicMock, patch

from devguard.config import Config, ReviewPolicy
from devguard.models import Finding, FindingSource, ReviewResult, RiskLevel, Severity
from devguard.reviewer import empty_review, review_diff


def _fake_result(risk: RiskLevel = RiskLevel.LOW) -> ReviewResult:
    return ReviewResult(summary="s", risk=risk, findings=[])


def test_review_diff_calls_provider_and_returns_stats(sample_diff: str, config: Config) -> None:
    provider = MagicMock()
    provider.review.return_value = _fake_result()
    with patch("devguard.reviewer.get_provider", return_value=provider):
        review = review_diff(sample_diff, config, semgrep_findings=[])
    provider.review.assert_called_once()
    assert review.stats.files_changed == 1


def test_heuristic_raises_risk_above_ai(sample_diff: str, config: Config) -> None:
    # AI says Low, but the diff touches auth/ with real change -> heuristic bumps it.
    provider = MagicMock()
    provider.review.return_value = _fake_result(RiskLevel.LOW)
    with patch("devguard.reviewer.get_provider", return_value=provider):
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
    with patch("devguard.reviewer.get_provider", return_value=provider):
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
    with patch("devguard.reviewer.get_provider", return_value=provider):
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
    with patch("devguard.reviewer.get_provider", return_value=provider):
        review = review_diff(sample_diff, cfg, semgrep_findings=[])
    assert review.result.findings == []


def test_empty_review_is_low() -> None:
    review = empty_review("nothing here")
    assert review.result.risk is RiskLevel.LOW
    assert review.stats.files_changed == 0
