"""Tests for building inline PR suggestions from findings."""

from __future__ import annotations

from gitowl.diff_utils import commentable_lines
from gitowl.models import Finding, FindingSource, Severity
from gitowl.suggest import build_inline_suggestions

# A two-file diff. In b/app.py the new-file lines 1-3 are added/context; in
# b/util.py line 1 is added. Nothing is commentable in a non-existent file.
DIFF = """\
diff --git a/app.py b/app.py
index 111..222 100644
--- a/app.py
+++ b/app.py
@@ -1,2 +1,3 @@
 import os
-x = md5(p)
+import hashlib
+x = hashlib.sha256(p)
diff --git a/util.py b/util.py
index 333..444 100644
--- a/util.py
+++ b/util.py
@@ -0,0 +1 @@
+y = 1
"""


def _finding(file: str | None, line: int | None, suggestion: str | None) -> Finding:
    return Finding(
        source=FindingSource.AI,
        severity=Severity.WARNING,
        title="Use sha256",
        message="md5 is weak",
        file=file,
        line=line,
        suggestion=suggestion,
    )


# --- commentable_lines -------------------------------------------------------


def test_commentable_lines_collects_added_and_context() -> None:
    lines = commentable_lines(DIFF)
    # app.py: line 1 (context 'import os'), 2 and 3 (added).
    assert lines["app.py"] == {1, 2, 3}
    assert lines["util.py"] == {1}


def test_commentable_lines_empty_on_garbage() -> None:
    assert commentable_lines("not a diff at all") == {}


# --- build_inline_suggestions ------------------------------------------------


def test_builds_suggestion_for_commentable_finding() -> None:
    findings = [_finding("app.py", 3, "x = hashlib.sha256(p)")]
    out = build_inline_suggestions(findings, DIFF)
    assert len(out) == 1
    assert out[0].path == "app.py"
    assert out[0].line == 3
    assert "```suggestion\nx = hashlib.sha256(p)\n```" in out[0].body
    assert "Use sha256" in out[0].body


def test_skips_finding_outside_diff() -> None:
    # Line 99 is not in any hunk -> dropped (would 422 on GitHub).
    findings = [_finding("app.py", 99, "fix")]
    assert build_inline_suggestions(findings, DIFF) == []


def test_skips_finding_without_suggestion() -> None:
    assert build_inline_suggestions([_finding("app.py", 3, None)], DIFF) == []


def test_skips_general_finding_without_file_or_line() -> None:
    assert build_inline_suggestions([_finding(None, None, "fix")], DIFF) == []
    assert build_inline_suggestions([_finding("app.py", None, "fix")], DIFF) == []


def test_mixed_findings_keep_only_eligible() -> None:
    findings = [
        _finding("app.py", 2, "import hashlib"),  # eligible
        _finding("app.py", 99, "nope"),  # outside diff
        _finding("util.py", 1, "y = 1"),  # eligible
        _finding(None, None, "general"),  # no anchor
    ]
    out = build_inline_suggestions(findings, DIFF)
    assert {(s.path, s.line) for s in out} == {("app.py", 2), ("util.py", 1)}
