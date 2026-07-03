"""Orchestrator: diff + Semgrep -> AI review -> risk-scored result.

This is the heart of DevGuard. It is deliberately I/O-light: callers supply the
diff and (optionally) Semgrep findings, and it returns a finished
:class:`ReviewResult`. The CLI and GitHub Action wire this to real sources.
"""

from __future__ import annotations

from dataclasses import dataclass

from devguard.ai_client import get_provider
from devguard.ai_client.base import AIProviderError
from devguard.config import Config
from devguard.diff_utils import DiffStats, compress_diff, parse_stats
from devguard.logging_config import get_logger
from devguard.models import Finding, ReviewResult, RiskLevel
from devguard.risk import heuristic_risk, reconcile

logger = get_logger(__name__)


@dataclass
class Review:
    """The full output of a review pass: the result plus the diff stats."""

    result: ReviewResult
    stats: DiffStats


def review_diff(
    diff: str,
    config: Config,
    *,
    semgrep_findings: list[Finding] | None = None,
) -> Review:
    """Run the full review pipeline over ``diff``.

    Steps: compute stats -> compress if oversized -> AI review -> reconcile the
    AI risk with an independent heuristic (taking the more severe).
    """
    findings = semgrep_findings or []
    stats = parse_stats(diff)
    logger.info(
        "Reviewing diff: %d file(s), +%d/-%d lines, %d semgrep finding(s)",
        stats.files_changed,
        stats.added_lines,
        stats.removed_lines,
        len(findings),
    )

    prepared = compress_diff(diff, config.max_diff_lines)

    provider = get_provider(config.ai)
    try:
        result = provider.review(prepared, findings)
    except AIProviderError:
        logger.exception("AI provider failed")
        raise

    heuristic = heuristic_risk(stats, result.findings)
    final_risk = reconcile(result.risk, heuristic)
    if final_risk is not result.risk:
        logger.info(
            "Risk raised from %s (AI) to %s (heuristic)",
            result.risk.value,
            final_risk.value,
        )
    result.risk = final_risk

    return Review(result=result, stats=stats)


def empty_review(reason: str) -> Review:
    """Return a trivial low-risk review (e.g. when a diff is empty)."""
    return Review(
        result=ReviewResult(summary=reason, risk=RiskLevel.LOW, findings=[]),
        stats=DiffStats(files_changed=0, added_lines=0, removed_lines=0, changed_files=[]),
    )
