"""Tests for heuristic risk scoring and reconciliation."""

from __future__ import annotations

from gitowl.diff_utils import DiffStats
from gitowl.models import Finding, FindingSource, RiskLevel, Severity
from gitowl.risk import heuristic_risk, reconcile, touches_sensitive_paths


def _stats(files: list[str], added: int = 10, removed: int = 0) -> DiffStats:
    return DiffStats(
        files_changed=len(files),
        added_lines=added,
        removed_lines=removed,
        changed_files=files,
    )


def test_error_finding_forces_high() -> None:
    finding = Finding(
        source=FindingSource.SEMGREP,
        severity=Severity.ERROR,
        title="sqli",
        message="SQL injection",
    )
    assert heuristic_risk(_stats(["app.py"]), [finding]) is RiskLevel.HIGH


def test_sensitive_path_with_substantial_change_is_high() -> None:
    assert heuristic_risk(_stats(["src/auth/login.py"], added=60), []) is RiskLevel.HIGH


def test_small_ordinary_change_is_low() -> None:
    assert heuristic_risk(_stats(["README.md"], added=3), []) is RiskLevel.LOW


def test_large_diff_is_at_least_medium() -> None:
    assert heuristic_risk(_stats(["a.py"], added=150), []) is RiskLevel.MEDIUM


def test_touches_sensitive_paths_detects_hints() -> None:
    hits = touches_sensitive_paths(["src/auth.py", "docs/readme.md", ".github/workflows/ci.yml"])
    assert "src/auth.py" in hits
    assert ".github/workflows/ci.yml" in hits
    assert "docs/readme.md" not in hits


def test_reconcile_takes_more_severe() -> None:
    assert reconcile(RiskLevel.LOW, RiskLevel.HIGH) is RiskLevel.HIGH
    assert reconcile(RiskLevel.HIGH, RiskLevel.LOW) is RiskLevel.HIGH
    assert reconcile(RiskLevel.MEDIUM, RiskLevel.MEDIUM) is RiskLevel.MEDIUM
