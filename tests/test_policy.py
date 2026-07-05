"""Tests for the review policy filter (severity threshold + ignore paths)."""

from __future__ import annotations

from gitowl.config import ReviewPolicy
from gitowl.models import Finding, FindingSource, Severity
from gitowl.policy import apply_policy, is_ignored, meets_threshold, severity_rank


def _finding(severity: Severity, file: str | None = "src/app.py") -> Finding:
    return Finding(
        source=FindingSource.AI,
        severity=severity,
        title="x",
        message="y",
        file=file,
        line=1,
    )


def test_severity_rank_orders_info_warning_error() -> None:
    assert severity_rank(Severity.INFO) < severity_rank(Severity.WARNING)
    assert severity_rank(Severity.WARNING) < severity_rank(Severity.ERROR)


def test_meets_threshold_inclusive() -> None:
    warn = _finding(Severity.WARNING)
    assert meets_threshold(warn, Severity.WARNING) is True  # equal passes
    assert meets_threshold(warn, Severity.ERROR) is False  # below fails
    assert meets_threshold(warn, Severity.INFO) is True  # above passes


def test_is_ignored_exact_and_nested_globs() -> None:
    patterns = ("tests/**", "**/*.md")
    assert is_ignored("tests/test_x.py", patterns) is True
    assert is_ignored("docs/readme.md", patterns) is True
    assert is_ignored("src/app.py", patterns) is False


def test_is_ignored_bare_pattern_matches_nested() -> None:
    # A bare "*.md" should still catch nested markdown files.
    assert is_ignored("src/notes.md", ("*.md",)) is True
    assert is_ignored("notes.md", ("*.md",)) is True


def test_is_ignored_normalizes_backslashes() -> None:
    # Windows-style paths in a diff should still match forward-slash globs.
    assert is_ignored("tests\\test_x.py", ("tests/**",)) is True


def test_is_ignored_empty_patterns_never_matches() -> None:
    assert is_ignored("anything.py", ()) is False


def test_apply_policy_default_keeps_everything() -> None:
    findings = [_finding(Severity.INFO), _finding(Severity.ERROR)]
    assert apply_policy(findings, ReviewPolicy()) == findings


def test_apply_policy_drops_below_threshold() -> None:
    findings = [
        _finding(Severity.INFO),
        _finding(Severity.WARNING),
        _finding(Severity.ERROR),
    ]
    kept = apply_policy(findings, ReviewPolicy(min_severity=Severity.WARNING))
    assert [f.severity for f in kept] == [Severity.WARNING, Severity.ERROR]


def test_apply_policy_drops_ignored_paths() -> None:
    findings = [
        _finding(Severity.ERROR, file="tests/test_x.py"),
        _finding(Severity.ERROR, file="src/app.py"),
    ]
    kept = apply_policy(findings, ReviewPolicy(ignore_paths=("tests/**",)))
    assert [f.file for f in kept] == ["src/app.py"]


def test_apply_policy_keeps_general_findings_without_file() -> None:
    # A finding with no file can't be path-filtered; only severity gates it.
    general = _finding(Severity.WARNING, file=None)
    kept = apply_policy([general], ReviewPolicy(ignore_paths=("**/*",)))
    assert kept == [general]


def test_apply_policy_severity_and_ignore_combined() -> None:
    findings = [
        _finding(Severity.INFO, file="src/app.py"),  # dropped: below threshold
        _finding(Severity.ERROR, file="tests/t.py"),  # dropped: ignored path
        _finding(Severity.ERROR, file="src/app.py"),  # kept
    ]
    policy = ReviewPolicy(min_severity=Severity.WARNING, ignore_paths=("tests/**",))
    kept = apply_policy(findings, policy)
    assert len(kept) == 1
    assert kept[0].file == "src/app.py"
    assert kept[0].severity is Severity.ERROR
