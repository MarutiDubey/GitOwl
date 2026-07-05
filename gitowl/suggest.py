"""Turn findings that carry a fix into inline PR review comments.

The summary comment renders ```suggestion blocks that a human can copy, but
GitHub's one-click "Commit suggestion" button only works on *inline review
comments* anchored to a diff line. This module selects the findings eligible
for that (they have a suggestion, a file, a line, and that line is actually in
the diff) and shapes them into the payload the Reviews API expects.
"""

from __future__ import annotations

from dataclasses import dataclass

from gitowl.diff_utils import commentable_lines
from gitowl.logging_config import get_logger
from gitowl.models import Finding

logger = get_logger(__name__)


@dataclass(frozen=True)
class InlineSuggestion:
    """A single inline review comment carrying a ```suggestion block.

    ``path`` / ``line`` anchor it to the new-file side of the diff; ``body`` is
    the Markdown GitHub renders (the suggestion block plus a short note).
    """

    path: str
    line: int
    body: str


def _body_for(finding: Finding) -> str:
    note = f"**{finding.title}** — {finding.message}".strip()
    return f"{note}\n\n```suggestion\n{finding.suggestion}\n```"


def build_inline_suggestions(findings: list[Finding], diff: str) -> list[InlineSuggestion]:
    """Select findings with a committable fix and map them to inline comments.

    A finding qualifies only when it has a suggestion, a file, a line, and that
    line is commentable in ``diff`` (added/context on the RIGHT side). Findings
    that fail any check are skipped and counted in a debug log, so a fix that
    points outside the diff never triggers a 422 from GitHub.
    """
    eligible = commentable_lines(diff)
    suggestions: list[InlineSuggestion] = []
    skipped = 0
    for f in findings:
        if not (f.suggestion and f.file and f.line is not None):
            continue
        if f.line not in eligible.get(f.file, set()):
            skipped += 1
            continue
        suggestions.append(InlineSuggestion(path=f.file, line=f.line, body=_body_for(f)))

    if skipped:
        logger.info("Skipped %d suggestion(s) pointing outside the diff.", skipped)
    return suggestions
