"""Tests for Markdown comment rendering."""

from __future__ import annotations

from devguard.comment import COMMENT_MARKER, render_comment
from devguard.diff_utils import DiffStats
from devguard.models import Finding, FindingSource, ReviewResult, RiskLevel, Severity


def _stats() -> DiffStats:
    return DiffStats(files_changed=2, added_lines=10, removed_lines=4, changed_files=["a", "b"])


def test_render_includes_marker_and_risk() -> None:
    result = ReviewResult(summary="Summary here.", risk=RiskLevel.HIGH, findings=[])
    body = render_comment(result, _stats())
    assert COMMENT_MARKER in body
    assert "High" in body
    assert "Summary here." in body
    assert "+10/-4" in body


def test_render_no_findings_shows_clean() -> None:
    result = ReviewResult(summary="s", risk=RiskLevel.LOW, findings=[])
    assert "No issues flagged" in render_comment(result, _stats())


def test_render_lists_findings_and_dismissed() -> None:
    result = ReviewResult(
        summary="s",
        risk=RiskLevel.MEDIUM,
        findings=[
            Finding(
                source=FindingSource.AI,
                severity=Severity.WARNING,
                title="Watch out",
                message="be careful",
                file="x.py",
                line=9,
            )
        ],
        dismissed=[
            Finding(
                source=FindingSource.SEMGREP,
                severity=Severity.INFO,
                title="fp",
                message="false positive",
                rule_id="rule.fp",
            )
        ],
    )
    body = render_comment(result, _stats())
    assert "Watch out" in body
    assert "x.py:9" in body
    assert "Dismissed as false positives" in body
    assert "rule.fp" in body
