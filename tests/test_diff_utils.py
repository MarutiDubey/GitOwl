"""Tests for diff parsing and compression."""

from __future__ import annotations

from gitowl.diff_utils import compress_diff, parse_stats


def test_parse_stats_counts_files_and_lines(sample_diff: str) -> None:
    stats = parse_stats(sample_diff)
    assert stats.files_changed == 1
    assert "auth/login.py" in stats.changed_files[0]
    assert stats.added_lines == 3
    assert stats.removed_lines == 1
    assert stats.total_changed_lines == 4


def test_parse_stats_empty_diff() -> None:
    stats = parse_stats("")
    assert stats.files_changed == 0
    assert stats.total_changed_lines == 0


def test_compress_diff_leaves_small_diffs_untouched(sample_diff: str) -> None:
    assert compress_diff(sample_diff, max_lines=2000) == sample_diff


def test_compress_diff_truncates_large_diffs() -> None:
    big = "diff --git a/x b/x\n" + "\n".join(f"+line {i}" for i in range(5000))
    out = compress_diff(big, max_lines=100)
    assert "GitOwl truncated" in out
    assert len(out.splitlines()) < 5000
    # Header line is always preserved.
    assert out.startswith("diff --git a/x b/x")
