"""Apply the repo review policy (severity threshold + ignore paths) to findings.

Pure functions, no I/O — the reviewer calls :func:`apply_policy` after the AI
returns its findings but *before* risk scoring, so ignored/low-severity findings
neither reach the PR comment nor inflate the risk level.
"""

from __future__ import annotations

from fnmatch import fnmatch

from gitowl.config import ReviewPolicy
from gitowl.logging_config import get_logger
from gitowl.models import Finding, Severity

logger = get_logger(__name__)

_SEVERITY_RANK = {Severity.INFO: 0, Severity.WARNING: 1, Severity.ERROR: 2}


def severity_rank(severity: Severity) -> int:
    """Ordinal rank so severities can be compared (info < warning < error)."""
    return _SEVERITY_RANK[severity]


def meets_threshold(finding: Finding, min_severity: Severity) -> bool:
    """True if ``finding`` is at least as severe as ``min_severity``."""
    return severity_rank(finding.severity) >= severity_rank(min_severity)


def is_ignored(path: str, patterns: tuple[str, ...]) -> bool:
    """True if ``path`` matches any glob in ``patterns``.

    Matching is done both against the raw pattern and a ``**/``-prefixed form so
    that a bare pattern like ``*.md`` also matches nested files (``src/x.md``),
    which is the behaviour users intuitively expect.
    """
    normalized = path.replace("\\", "/")
    for pattern in patterns:
        if fnmatch(normalized, pattern) or fnmatch(normalized, f"**/{pattern}"):
            return True
    return False


def apply_policy(findings: list[Finding], policy: ReviewPolicy) -> list[Finding]:
    """Return the findings that survive the policy.

    A finding is dropped when its file matches an ignore pattern, or when its
    severity is below ``policy.min_severity``. Findings with no file (general
    observations) are never path-filtered — only the severity gate applies.
    """
    kept: list[Finding] = []
    for finding in findings:
        if finding.file and is_ignored(finding.file, policy.ignore_paths):
            continue
        if not meets_threshold(finding, policy.min_severity):
            continue
        kept.append(finding)

    dropped = len(findings) - len(kept)
    if dropped:
        logger.info(
            "Policy dropped %d of %d finding(s) (min_severity=%s, %d ignore pattern(s))",
            dropped,
            len(findings),
            policy.min_severity.value,
            len(policy.ignore_paths),
        )
    return kept
