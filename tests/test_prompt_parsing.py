"""Tests for AI response parsing (the fragile boundary with the model)."""

from __future__ import annotations

import json

import pytest

from devguard.ai_client.prompt import build_user_prompt, parse_review_response
from devguard.models import Finding, FindingSource, RiskLevel, Severity


def _semgrep(rule_id: str) -> Finding:
    return Finding(
        source=FindingSource.SEMGREP,
        severity=Severity.WARNING,
        title=rule_id,
        message="something",
        file="a.py",
        line=1,
        rule_id=rule_id,
    )


def test_parse_plain_json() -> None:
    content = json.dumps(
        {
            "summary": "Looks fine.",
            "risk": "Low",
            "findings": [
                {"severity": "error", "title": "Bug", "message": "boom", "file": "a.py", "line": 3}
            ],
            "dismissed_rule_ids": [],
        }
    )
    result = parse_review_response(content, [])
    assert result.risk is RiskLevel.LOW
    assert result.summary == "Looks fine."
    assert result.findings[0].severity is Severity.ERROR
    assert result.findings[0].line == 3


def test_parse_json_wrapped_in_code_fence() -> None:
    content = "```json\n" + json.dumps({"summary": "s", "risk": "High", "findings": []}) + "\n```"
    result = parse_review_response(content, [])
    assert result.risk is RiskLevel.HIGH


def test_parse_tolerates_prose_around_json() -> None:
    content = (
        'Sure! Here is my review:\n{"summary":"s","risk":"Medium","findings":[]}\nHope that helps.'
    )
    result = parse_review_response(content, [])
    assert result.risk is RiskLevel.MEDIUM


def test_dismissed_rule_ids_move_findings_to_dismissed() -> None:
    content = json.dumps(
        {"summary": "s", "risk": "Low", "findings": [], "dismissed_rule_ids": ["python.lang.fp"]}
    )
    findings = [_semgrep("python.lang.fp"), _semgrep("python.lang.real")]
    result = parse_review_response(content, findings)
    kept_ids = {f.rule_id for f in result.findings}
    dismissed_ids = {f.rule_id for f in result.dismissed}
    assert "python.lang.real" in kept_ids
    assert "python.lang.fp" in dismissed_ids


def test_invalid_risk_falls_back_to_medium() -> None:
    content = json.dumps({"summary": "s", "risk": "Catastrophic", "findings": []})
    assert parse_review_response(content, []).risk is RiskLevel.MEDIUM


def test_no_json_raises() -> None:
    with pytest.raises(ValueError):
        parse_review_response("I refuse to answer.", [])


def test_build_user_prompt_includes_findings() -> None:
    prompt = build_user_prompt("diff --git a/x b/x", [_semgrep("rule.x")])
    assert "rule.x" in prompt
    assert "Unified diff" in prompt


def test_build_user_prompt_handles_no_findings() -> None:
    prompt = build_user_prompt("diff", [])
    assert "(none)" in prompt
