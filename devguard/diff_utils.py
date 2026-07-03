"""Diff parsing and compression helpers.

Large PRs can blow past model context limits, so we compress diffs beyond
``MAX_DIFF_LINES`` by truncating per-file hunks while preserving structure.
"""

from __future__ import annotations

from dataclasses import dataclass

from unidiff import PatchSet
from unidiff.errors import UnidiffParseError

from devguard.logging_config import get_logger

logger = get_logger(__name__)


@dataclass
class DiffStats:
    """Summary statistics for a diff, used by risk scoring."""

    files_changed: int
    added_lines: int
    removed_lines: int
    changed_files: list[str]

    @property
    def total_changed_lines(self) -> int:
        return self.added_lines + self.removed_lines


def parse_stats(diff: str) -> DiffStats:
    """Compute file/line statistics from a unified diff.

    Falls back to a rough line-count scan if the diff cannot be parsed.
    """
    try:
        patch = PatchSet(diff)
    except (UnidiffParseError, Exception) as exc:  # noqa: BLE001 - defensive
        logger.warning("Falling back to naive diff stats: %s", exc)
        return _naive_stats(diff)

    changed_files = [pf.path for pf in patch]
    added = sum(pf.added for pf in patch)
    removed = sum(pf.removed for pf in patch)
    return DiffStats(
        files_changed=len(changed_files),
        added_lines=added,
        removed_lines=removed,
        changed_files=changed_files,
    )


def _naive_stats(diff: str) -> DiffStats:
    added = removed = 0
    files: set[str] = set()
    for line in diff.splitlines():
        if line.startswith("+++ ") or line.startswith("--- "):
            path = line[4:].strip()
            if path and path not in ("/dev/null",):
                files.add(path.removeprefix("a/").removeprefix("b/"))
        elif line.startswith("+") and not line.startswith("+++"):
            added += 1
        elif line.startswith("-") and not line.startswith("---"):
            removed += 1
    return DiffStats(
        files_changed=len(files),
        added_lines=added,
        removed_lines=removed,
        changed_files=sorted(files),
    )


def compress_diff(diff: str, max_lines: int) -> str:
    """Truncate ``diff`` to roughly ``max_lines`` lines, keeping headers.

    When a diff is too large we keep every file/hunk header and as many hunk
    lines as fit, appending a marker where content was elided. This keeps the
    model oriented without exceeding context limits.
    """
    lines = diff.splitlines()
    if len(lines) <= max_lines:
        return diff

    logger.info("Compressing diff from %d to ~%d lines", len(lines), max_lines)
    kept: list[str] = []
    budget = max_lines
    elided = 0
    for line in lines:
        is_header = line.startswith(("diff ", "index ", "--- ", "+++ ", "@@"))
        if budget > 0 or is_header:
            kept.append(line)
            if not is_header:
                budget -= 1
        else:
            elided += 1
    if elided:
        kept.append(f"\n... [DevGuard truncated {elided} lines to fit context limit] ...")
    return "\n".join(kept)
