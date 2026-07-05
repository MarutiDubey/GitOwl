"""Run Semgrep and normalise its output into GitOwl ``Finding`` objects."""

from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
from pathlib import Path

from gitowl.logging_config import get_logger
from gitowl.models import Finding, FindingSource, Severity

logger = get_logger(__name__)

# Map Semgrep severity strings to our Severity enum.
_SEVERITY_MAP = {
    "ERROR": Severity.ERROR,
    "WARNING": Severity.WARNING,
    "INFO": Severity.INFO,
}


class SemgrepError(RuntimeError):
    """Raised when Semgrep cannot be invoked (not the same as findings)."""


def is_available() -> bool:
    """Return True if the ``semgrep`` executable is on PATH."""
    return shutil.which("semgrep") is not None


def scan_paths(
    paths: list[str],
    *,
    config: str = "auto",
    timeout_seconds: int = 60,
) -> list[Finding]:
    """Run ``semgrep --config <config>`` over ``paths`` and return findings.

    Returns an empty list (not an error) when Semgrep runs but finds nothing.
    Raises :class:`SemgrepError` only when Semgrep cannot run at all.
    """
    if not is_available():
        raise SemgrepError(
            "semgrep is not installed or not on PATH. Install it with `pip install semgrep`."
        )

    cmd = [
        "semgrep",
        "--config",
        config,
        "--json",
        "--quiet",
        "--timeout",
        str(timeout_seconds),
        *paths,
    ]
    logger.info("Running semgrep: %s", " ".join(cmd))
    try:
        proc = subprocess.run(  # noqa: S603 - args are controlled
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout_seconds + 30,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        raise SemgrepError(f"semgrep timed out after {timeout_seconds}s") from exc
    except OSError as exc:
        raise SemgrepError(f"failed to run semgrep: {exc}") from exc

    # Semgrep exits non-zero when findings exist; only treat a missing/invalid
    # JSON payload as a hard failure.
    if not proc.stdout.strip():
        if proc.returncode not in (0, 1):
            raise SemgrepError(f"semgrep exited {proc.returncode}: {proc.stderr[:300]}")
        return []

    return parse_semgrep_json(proc.stdout)


def parse_semgrep_json(raw: str) -> list[Finding]:
    """Convert Semgrep's ``--json`` output into ``Finding`` objects."""
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise SemgrepError(f"could not parse semgrep JSON output: {exc}") from exc

    findings: list[Finding] = []
    for result in data.get("results", []):
        extra = result.get("extra", {})
        severity = _SEVERITY_MAP.get(
            str(extra.get("severity", "WARNING")).upper(), Severity.WARNING
        )
        rule_id = result.get("check_id", "")
        message = extra.get("message", "").strip() or rule_id
        start = result.get("start", {})
        findings.append(
            Finding(
                source=FindingSource.SEMGREP,
                severity=severity,
                title=rule_id.split(".")[-1] if rule_id else "semgrep-finding",
                message=message,
                file=result.get("path"),
                line=start.get("line"),
                rule_id=rule_id or None,
            )
        )
    logger.info("Semgrep produced %d finding(s)", len(findings))
    return findings


def scan_diff_files(diff_files: list[str], **kwargs: object) -> list[Finding]:
    """Scan only files that exist locally (skips deletions/renames cleanly)."""
    existing = [p for p in diff_files if Path(p).is_file()]
    if not existing:
        logger.info("No changed files exist locally to scan with semgrep")
        return []
    return scan_paths(existing, **kwargs)  # type: ignore[arg-type]


def write_temp_and_scan(filename: str, content: str, **kwargs: object) -> list[Finding]:
    """Write ``content`` to a temp file named like ``filename`` and scan it.

    Useful when reviewing a diff without a full checkout — we materialise the
    post-change file content so Semgrep has something to analyse.
    """
    suffix = Path(filename).suffix or ".txt"
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=suffix, delete=False, encoding="utf-8"
    ) as tmp:
        tmp.write(content)
        tmp_path = tmp.name
    try:
        return scan_paths([tmp_path], **kwargs)  # type: ignore[arg-type]
    finally:
        Path(tmp_path).unlink(missing_ok=True)
