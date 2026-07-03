"""Tests for Semgrep output parsing (invocation is mocked/skipped)."""

from __future__ import annotations

import json

import pytest

from devguard.models import FindingSource, Severity
from devguard.semgrep_runner import SemgrepError, parse_semgrep_json


def test_parse_semgrep_json_maps_fields() -> None:
    raw = json.dumps(
        {
            "results": [
                {
                    "check_id": "python.lang.security.audit.dangerous-exec",
                    "path": "app.py",
                    "start": {"line": 12},
                    "extra": {"severity": "ERROR", "message": "Avoid exec()"},
                }
            ]
        }
    )
    findings = parse_semgrep_json(raw)
    assert len(findings) == 1
    f = findings[0]
    assert f.source is FindingSource.SEMGREP
    assert f.severity is Severity.ERROR
    assert f.file == "app.py"
    assert f.line == 12
    assert f.rule_id == "python.lang.security.audit.dangerous-exec"
    assert f.title == "dangerous-exec"


def test_parse_semgrep_json_empty_results() -> None:
    assert parse_semgrep_json(json.dumps({"results": []})) == []


def test_parse_semgrep_json_invalid_raises() -> None:
    with pytest.raises(SemgrepError):
        parse_semgrep_json("not json")
