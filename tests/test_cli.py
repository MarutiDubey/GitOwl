"""End-to-end tests for the CLI entry point (`gitowl.cli.main`).

The AI, Semgrep, and GitHub layers are stubbed so these exercise argument
parsing, command dispatch, exit codes, and output wiring — not live services.
"""

from __future__ import annotations

import dataclasses
import io
from unittest.mock import MagicMock, patch

import pytest

from gitowl.cli import main
from gitowl.diff_utils import DiffStats
from gitowl.github_client import GitHubError
from gitowl.models import PrDescription, ReviewResult, RiskLevel
from gitowl.reviewer import Review


def _canned_desc() -> PrDescription:
    return PrDescription(title="Add x", summary="Adds x.", changes=["did x"])


def _canned_review(summary: str = "Looks fine.") -> Review:
    return Review(
        result=ReviewResult(summary=summary, risk=RiskLevel.LOW, findings=[]),
        stats=DiffStats(files_changed=1, added_lines=1, removed_lines=0, changed_files=["a.py"]),
    )


@pytest.fixture
def patched_config(config):
    """Make `load_config()` in the CLI return the test fixture, no env reads."""
    with patch("gitowl.cli.load_config", return_value=config):
        yield config


# --- providers ---------------------------------------------------------------


def test_providers_lists_and_marks_active(patched_config, capsys) -> None:
    assert main(["providers"]) == 0
    out = capsys.readouterr().out
    assert "Available AI providers:" in out
    assert "openrouter (active)" in out


# --- review-diff -------------------------------------------------------------


def test_review_diff_from_file(patched_config, tmp_path, capsys) -> None:
    diff = tmp_path / "change.diff"
    diff.write_text("diff --git a/a.py b/a.py\n+x = 1\n", encoding="utf-8")
    with patch("gitowl.cli.review_diff", return_value=_canned_review("From file.")) as rv:
        assert main(["review-diff", str(diff), "--no-semgrep"]) == 0
    assert "From file." in capsys.readouterr().out
    # --no-semgrep means findings are passed empty, not scanned.
    assert rv.call_args.kwargs["semgrep_findings"] == []


def test_review_diff_empty_file_short_circuits(patched_config, tmp_path, capsys) -> None:
    diff = tmp_path / "empty.diff"
    diff.write_text("   \n", encoding="utf-8")
    with patch("gitowl.cli.review_diff") as rv:
        assert main(["review-diff", str(diff), "--no-semgrep"]) == 0
    rv.assert_not_called()
    assert "nothing to review" in capsys.readouterr().out


def test_review_diff_from_stdin(patched_config, capsys) -> None:
    with (
        patch("sys.stdin", io.StringIO("diff --git a/a.py b/a.py\n+x = 1\n")),
        patch("gitowl.cli.review_diff", return_value=_canned_review("From stdin.")),
    ):
        assert main(["review-diff", "-", "--no-semgrep"]) == 0
    assert "From stdin." in capsys.readouterr().out


def test_review_diff_missing_file_is_config_error(patched_config) -> None:
    assert main(["review-diff", "does/not/exist.diff", "--no-semgrep"]) == 2


def test_review_diff_runs_semgrep_when_not_disabled(patched_config, tmp_path) -> None:
    diff = tmp_path / "change.diff"
    diff.write_text("diff --git a/a.py b/a.py\n+x = 1\n", encoding="utf-8")
    with (
        patch("gitowl.cli._run_semgrep_if_available", return_value=[]) as scan,
        patch("gitowl.cli.review_diff", return_value=_canned_review()),
    ):
        assert main(["review-diff", str(diff)]) == 0
    scan.assert_called_once()


def test_ai_provider_error_exits_three(patched_config, tmp_path) -> None:
    from gitowl.ai_client.base import AIProviderError

    diff = tmp_path / "change.diff"
    diff.write_text("diff --git a/a.py b/a.py\n+x = 1\n", encoding="utf-8")
    with patch("gitowl.cli.review_diff", side_effect=AIProviderError("down")):
        assert main(["review-diff", str(diff), "--no-semgrep"]) == 3


# --- review-pr ---------------------------------------------------------------


def test_review_pr_without_token_is_config_error(config) -> None:
    no_token = dataclasses.replace(config, github_token="")
    with patch("gitowl.cli.load_config", return_value=no_token):
        assert main(["review-pr", "owner/repo", "5"]) == 2


def test_review_pr_prints_body_without_posting(patched_config, capsys) -> None:
    client = MagicMock()
    client.fetch_pr_diff.return_value = "diff --git a/a.py b/a.py\n+x = 1\n"
    with (
        patch("gitowl.github_client.GitHubClient", return_value=client),
        patch("gitowl.cli.review_diff", return_value=_canned_review("PR body.")),
    ):
        assert main(["review-pr", "owner/repo", "5", "--no-semgrep"]) == 0
    client.post_or_update_comment.assert_not_called()
    assert "PR body." in capsys.readouterr().out


def test_review_pr_post_flag_posts_comment(patched_config, capsys) -> None:
    client = MagicMock()
    client.fetch_pr_diff.return_value = "diff --git a/a.py b/a.py\n+x = 1\n"
    with (
        patch("gitowl.github_client.GitHubClient", return_value=client),
        patch("gitowl.cli.review_diff", return_value=_canned_review()),
    ):
        assert main(["review-pr", "owner/repo", "5", "--post", "--no-semgrep"]) == 0
    client.post_or_update_comment.assert_called_once()
    assert "Posted review to owner/repo#5" in capsys.readouterr().out


def test_review_pr_suggest_posts_inline(patched_config, capsys) -> None:
    from gitowl.suggest import InlineSuggestion

    client = MagicMock()
    client.fetch_pr_diff.return_value = "diff --git a/a.py b/a.py\n+x = 1\n"
    client.post_review_comments.return_value = 1
    canned = _canned_review()
    with (
        patch("gitowl.github_client.GitHubClient", return_value=client),
        patch("gitowl.cli.review_diff", return_value=canned),
        patch(
            "gitowl.suggest.build_inline_suggestions",
            return_value=[InlineSuggestion(path="a.py", line=1, body="```suggestion\nx\n```")],
        ),
    ):
        assert main(["review-pr", "owner/repo", "5", "--post", "--suggest", "--no-semgrep"]) == 0
    client.post_review_comments.assert_called_once()
    assert "Posted 1 inline suggestion(s)." in capsys.readouterr().out


def test_review_pr_suggest_without_post_does_not_post(patched_config) -> None:
    # --suggest only fires alongside --post; without --post nothing is sent.
    client = MagicMock()
    client.fetch_pr_diff.return_value = "diff --git a/a.py b/a.py\n+x = 1\n"
    with (
        patch("gitowl.github_client.GitHubClient", return_value=client),
        patch("gitowl.cli.review_diff", return_value=_canned_review()),
    ):
        assert main(["review-pr", "owner/repo", "5", "--suggest", "--no-semgrep"]) == 0
    client.post_review_comments.assert_not_called()


def test_review_pr_empty_diff_short_circuits(patched_config, capsys) -> None:
    client = MagicMock()
    client.fetch_pr_diff.return_value = "   \n"
    with (
        patch("gitowl.github_client.GitHubClient", return_value=client),
        patch("gitowl.cli.review_diff") as rv,
    ):
        assert main(["review-pr", "owner/repo", "5", "--no-semgrep"]) == 0
    rv.assert_not_called()
    assert "nothing to review" in capsys.readouterr().out


def test_review_pr_fetch_failure_exits_two(patched_config) -> None:
    client = MagicMock()
    client.fetch_pr_diff.side_effect = GitHubError("404")
    with patch("gitowl.github_client.GitHubClient", return_value=client):
        assert main(["review-pr", "owner/repo", "5"]) == 2


def test_review_pr_post_failure_exits_two(patched_config) -> None:
    client = MagicMock()
    client.fetch_pr_diff.return_value = "diff --git a/a.py b/a.py\n+x = 1\n"
    client.post_or_update_comment.side_effect = GitHubError("403")
    with (
        patch("gitowl.github_client.GitHubClient", return_value=client),
        patch("gitowl.cli.review_diff", return_value=_canned_review()),
    ):
        assert main(["review-pr", "owner/repo", "5", "--post", "--no-semgrep"]) == 2


# --- describe-diff -----------------------------------------------------------


def test_describe_diff_prints_description(patched_config, tmp_path, capsys) -> None:
    diff = tmp_path / "change.diff"
    diff.write_text("diff --git a/a.py b/a.py\n+x = 1\n", encoding="utf-8")
    with patch("gitowl.cli.describe_diff", return_value=_canned_desc()):
        assert main(["describe-diff", str(diff)]) == 0
    out = capsys.readouterr().out
    assert "## Add x" in out
    assert "- did x" in out


def test_describe_diff_empty_short_circuits(patched_config, tmp_path, capsys) -> None:
    diff = tmp_path / "empty.diff"
    diff.write_text("  \n", encoding="utf-8")
    with patch("gitowl.cli.describe_diff") as dd:
        assert main(["describe-diff", str(diff)]) == 0
    dd.assert_not_called()
    assert "nothing to describe" in capsys.readouterr().out


# --- describe-pr -------------------------------------------------------------


def test_describe_pr_prints_without_posting(patched_config, capsys) -> None:
    client = MagicMock()
    client.fetch_pr_diff.return_value = "diff --git a/a.py b/a.py\n+x = 1\n"
    with (
        patch("gitowl.github_client.GitHubClient", return_value=client),
        patch("gitowl.cli.describe_diff", return_value=_canned_desc()),
    ):
        assert main(["describe-pr", "owner/repo", "5"]) == 0
    client.update_pr_body.assert_not_called()
    assert "## Add x" in capsys.readouterr().out


def test_describe_pr_post_updates_body(patched_config, capsys) -> None:
    client = MagicMock()
    client.fetch_pr_diff.return_value = "diff --git a/a.py b/a.py\n+x = 1\n"
    client.fetch_pr_body.return_value = "Author text."
    with (
        patch("gitowl.github_client.GitHubClient", return_value=client),
        patch("gitowl.cli.describe_diff", return_value=_canned_desc()),
    ):
        assert main(["describe-pr", "owner/repo", "5", "--post"]) == 0
    client.update_pr_body.assert_called_once()
    # The merged body preserves the author's text and adds our section.
    posted = client.update_pr_body.call_args.args[2]
    assert "Author text." in posted
    assert "## Add x" in posted
    assert "Updated PR description on owner/repo#5" in capsys.readouterr().out


def test_describe_pr_without_token_is_config_error(config) -> None:
    no_token = dataclasses.replace(config, github_token="")
    with patch("gitowl.cli.load_config", return_value=no_token):
        assert main(["describe-pr", "owner/repo", "5"]) == 2


def test_describe_pr_post_failure_exits_two(patched_config) -> None:
    client = MagicMock()
    client.fetch_pr_diff.return_value = "diff --git a/a.py b/a.py\n+x = 1\n"
    client.fetch_pr_body.return_value = ""
    client.update_pr_body.side_effect = GitHubError("403")
    with (
        patch("gitowl.github_client.GitHubClient", return_value=client),
        patch("gitowl.cli.describe_diff", return_value=_canned_desc()),
    ):
        assert main(["describe-pr", "owner/repo", "5", "--post"]) == 2


# --- semgrep helper ----------------------------------------------------------


def test_semgrep_helper_returns_empty_when_unavailable(config) -> None:
    from gitowl import cli

    with patch("gitowl.semgrep_runner.is_available", return_value=False):
        assert cli._run_semgrep_if_available("diff --git a/a.py b/a.py\n", config) == []


def test_semgrep_helper_scans_changed_files_when_available(config) -> None:
    from gitowl import cli

    diff = "diff --git a/a.py b/a.py\n--- a/a.py\n+++ b/a.py\n@@ -1 +1 @@\n+x = 1\n"
    with (
        patch("gitowl.semgrep_runner.is_available", return_value=True),
        patch("gitowl.semgrep_runner.scan_diff_files", return_value=[]) as scan,
    ):
        assert cli._run_semgrep_if_available(diff, config) == []
    scan.assert_called_once()


def test_semgrep_helper_swallows_semgrep_errors(config) -> None:
    from gitowl import cli
    from gitowl.semgrep_runner import SemgrepError

    diff = "diff --git a/a.py b/a.py\n--- a/a.py\n+++ b/a.py\n@@ -1 +1 @@\n+x = 1\n"
    with (
        patch("gitowl.semgrep_runner.is_available", return_value=True),
        patch("gitowl.semgrep_runner.scan_diff_files", side_effect=SemgrepError("crashed")),
    ):
        assert cli._run_semgrep_if_available(diff, config) == []


# --- top-level parsing -------------------------------------------------------


def test_version_flag_exits_zero(capsys) -> None:
    with pytest.raises(SystemExit) as exc:
        main(["--version"])
    assert exc.value.code == 0
    assert "GitOwl" in capsys.readouterr().out


def test_no_subcommand_errors() -> None:
    with pytest.raises(SystemExit) as exc:
        main([])
    assert exc.value.code == 2
