"""Heuristic risk scoring combining diff size, files touched, and findings.

The AI proposes a risk level; this module computes an independent heuristic
score so the two can be reconciled (we take the higher of the two). That guards
against a model that under-reports risk.
"""

from __future__ import annotations

from gitowl.diff_utils import DiffStats
from gitowl.models import Finding, RiskLevel, Severity

# File path fragments that tend to indicate higher-risk changes.
_SENSITIVE_HINTS = (
    "auth",
    "login",
    "password",
    "secret",
    "token",
    "crypto",
    "security",
    "payment",
    "migration",
    "Dockerfile",
    ".github/workflows",
    "requirements",
    "settings",
)

_RANK = {RiskLevel.LOW: 0, RiskLevel.MEDIUM: 1, RiskLevel.HIGH: 2}


def touches_sensitive_paths(changed_files: list[str]) -> list[str]:
    """Return the subset of changed files that match sensitive-path hints."""
    hits = []
    for path in changed_files:
        lowered = path.lower()
        if any(hint.lower() in lowered for hint in _SENSITIVE_HINTS):
            hits.append(path)
    return hits


def heuristic_risk(stats: DiffStats, findings: list[Finding]) -> RiskLevel:
    """Compute a risk level from diff size, sensitive paths, and finding severity."""
    error_findings = sum(1 for f in findings if f.severity is Severity.ERROR)
    sensitive = touches_sensitive_paths(stats.changed_files)

    # High: any error-severity finding, or sensitive path + substantial change.
    if error_findings > 0:
        return RiskLevel.HIGH
    if sensitive and stats.total_changed_lines >= 50:
        return RiskLevel.HIGH
    if stats.total_changed_lines >= 500 or stats.files_changed >= 15:
        return RiskLevel.HIGH

    # Medium: warnings present, sensitive paths, or a moderately large diff.
    warning_findings = sum(1 for f in findings if f.severity is Severity.WARNING)
    if warning_findings > 0 or sensitive:
        return RiskLevel.MEDIUM
    if stats.total_changed_lines >= 100 or stats.files_changed >= 5:
        return RiskLevel.MEDIUM

    return RiskLevel.LOW


def reconcile(ai_risk: RiskLevel, heuristic: RiskLevel) -> RiskLevel:
    """Return the more severe of the AI's risk and the heuristic risk."""
    return ai_risk if _RANK[ai_risk] >= _RANK[heuristic] else heuristic
