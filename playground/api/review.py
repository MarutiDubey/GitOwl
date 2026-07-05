"""Playground API: review a pasted diff with DevGuard's AI-only review path.

A Vercel Python serverless function — this module's ``app`` is the entry
point Vercel maps to ``/api/review``. Deliberately thin: it reuses
``devguard.reviewer.review_diff`` directly (no reimplementation of review
logic) with Semgrep skipped, since pasted snippets aren't a checked-out repo
and Semgrep isn't installed on the function host.
"""

from __future__ import annotations

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from devguard.ai_client.base import AIProviderError
from devguard.config import ConfigError, load_config
from devguard.reviewer import review_diff

app = FastAPI()

# Public, unauthenticated endpoint with no owner approving each request (unlike
# a real PR review) -- bound AI cost from abuse before review_diff's own
# max_diff_lines compression even runs.
MAX_LINES = 500


class ReviewRequest(BaseModel):
    diff: str


class FindingOut(BaseModel):
    severity: str
    title: str
    message: str
    file: str | None
    line: int | None
    suggestion: str | None


class ReviewResponse(BaseModel):
    risk: str
    summary: str
    findings: list[FindingOut]
    files_changed: int
    added_lines: int
    removed_lines: int


@app.post("/api/review", response_model=ReviewResponse)
def review(req: ReviewRequest) -> ReviewResponse:
    diff = req.diff.strip()
    if not diff:
        raise HTTPException(400, "diff is empty")
    if diff.count("\n") > MAX_LINES:
        raise HTTPException(413, f"diff too large (max {MAX_LINES} lines)")

    try:
        config = load_config()
    except ConfigError as exc:
        raise HTTPException(500, str(exc)) from exc

    try:
        result = review_diff(diff, config, semgrep_findings=[])
    except AIProviderError:
        raise HTTPException(502, "review failed upstream") from None

    findings = [
        FindingOut(
            severity=f.severity.value,
            title=f.title,
            message=f.message,
            file=f.file,
            line=f.line,
            suggestion=f.suggestion,
        )
        for f in result.result.findings
    ]
    return ReviewResponse(
        risk=result.result.risk.value,
        summary=result.result.summary,
        findings=findings,
        files_changed=result.stats.files_changed,
        added_lines=result.stats.added_lines,
        removed_lines=result.stats.removed_lines,
    )
