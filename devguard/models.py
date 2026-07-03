"""Shared data models used across the review pipeline.

These are the contracts every layer speaks in:
  - `Finding`     : a single issue (from Semgrep or the AI)
  - `ReviewResult`: the AI layer's structured output for a diff
  - `RiskLevel`   : the overall PR risk score
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class RiskLevel(str, Enum):
    """Overall risk score for a pull request."""

    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"


class Severity(str, Enum):
    """Severity of an individual finding."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


class FindingSource(str, Enum):
    """Where a finding originated."""

    SEMGREP = "semgrep"
    AI = "ai"


@dataclass
class Finding:
    """A single issue flagged against the diff."""

    source: FindingSource
    severity: Severity
    title: str
    message: str
    file: str | None = None
    line: int | None = None
    rule_id: str | None = None

    def location(self) -> str:
        """Human-readable file:line location, or '(general)' when unattached."""
        if not self.file:
            return "(general)"
        return f"{self.file}:{self.line}" if self.line else self.file


@dataclass
class ReviewResult:
    """Structured output of an AI review pass over a diff."""

    summary: str
    risk: RiskLevel
    findings: list[Finding] = field(default_factory=list)
    # Semgrep findings the AI judged to be false positives (kept for transparency).
    dismissed: list[Finding] = field(default_factory=list)
