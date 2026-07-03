"""Tests for the GitHub REST client with the HTTP layer mocked — never hits live GitHub."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import httpx
import pytest

from devguard.comment import COMMENT_MARKER
from devguard.github_client import GitHubClient, GitHubError


def _ok_response(*, text: str = "", json_body: object = None) -> MagicMock:
    resp = MagicMock()
    resp.raise_for_status.return_value = None
    resp.text = text
    resp.json.return_value = json_body if json_body is not None else []
    return resp


def _failing_response() -> MagicMock:
    resp = MagicMock()
    resp.raise_for_status.side_effect = httpx.HTTPError("boom")
    return resp


def test_constructor_rejects_empty_token() -> None:
    with pytest.raises(GitHubError, match="token is required"):
        GitHubClient("")


def test_api_root_trailing_slash_is_stripped() -> None:
    client = GitHubClient("t", api_root="https://example.test/")
    assert client._api_root == "https://example.test"


def test_headers_carry_bearer_token_and_api_version() -> None:
    client = GitHubClient("secret")
    headers = client._headers()
    assert headers["Authorization"] == "Bearer secret"
    assert headers["X-GitHub-Api-Version"] == "2022-11-28"


def test_fetch_pr_diff_returns_text_and_requests_diff_media_type() -> None:
    client = GitHubClient("t")
    with patch("devguard.github_client.httpx.get", return_value=_ok_response(text="DIFF")) as get:
        assert client.fetch_pr_diff("owner/repo", 7) == "DIFF"
    url = get.call_args.args[0]
    accept = get.call_args.kwargs["headers"]["Accept"]
    assert url.endswith("/repos/owner/repo/pulls/7")
    assert accept == "application/vnd.github.v3.diff"


def test_fetch_pr_diff_wraps_http_errors() -> None:
    client = GitHubClient("t")
    with patch("devguard.github_client.httpx.get", return_value=_failing_response()):
        with pytest.raises(GitHubError, match="failed to fetch PR diff"):
            client.fetch_pr_diff("owner/repo", 7)


def test_post_creates_new_comment_when_none_exists() -> None:
    client = GitHubClient("t")
    with (
        patch("devguard.github_client.httpx.get", return_value=_ok_response(json_body=[])),
        patch("devguard.github_client.httpx.post", return_value=_ok_response()) as post,
        patch("devguard.github_client.httpx.patch") as patch_call,
    ):
        client.post_or_update_comment("owner/repo", 3, "hello")
    assert post.called
    assert not patch_call.called
    assert post.call_args.args[0].endswith("/repos/owner/repo/issues/3/comments")


def test_post_updates_existing_devguard_comment() -> None:
    client = GitHubClient("t")
    existing = [{"id": 42, "body": f"stale {COMMENT_MARKER}"}]
    with (
        patch("devguard.github_client.httpx.get", return_value=_ok_response(json_body=existing)),
        patch("devguard.github_client.httpx.post") as post,
        patch("devguard.github_client.httpx.patch", return_value=_ok_response()) as patch_call,
    ):
        client.post_or_update_comment("owner/repo", 3, "fresh")
    assert patch_call.called
    assert not post.called
    assert patch_call.call_args.args[0].endswith("/repos/owner/repo/issues/comments/42")


def test_post_falls_back_to_create_when_listing_comments_fails() -> None:
    """A failed comment-list is non-fatal: we log and post a fresh comment."""
    client = GitHubClient("t")
    with (
        patch("devguard.github_client.httpx.get", return_value=_failing_response()),
        patch("devguard.github_client.httpx.post", return_value=_ok_response()) as post,
        patch("devguard.github_client.httpx.patch") as patch_call,
    ):
        client.post_or_update_comment("owner/repo", 3, "hello")
    assert post.called
    assert not patch_call.called


def test_post_wraps_http_errors() -> None:
    client = GitHubClient("t")
    with (
        patch("devguard.github_client.httpx.get", return_value=_ok_response(json_body=[])),
        patch("devguard.github_client.httpx.post", return_value=_failing_response()),
    ):
        with pytest.raises(GitHubError, match="failed to post PR comment"):
            client.post_or_update_comment("owner/repo", 3, "hello")


def test_existing_comment_ignores_non_devguard_comments() -> None:
    client = GitHubClient("t")
    unrelated = [{"id": 1, "body": "just a normal review"}]
    with (
        patch("devguard.github_client.httpx.get", return_value=_ok_response(json_body=unrelated)),
        patch("devguard.github_client.httpx.post", return_value=_ok_response()) as post,
        patch("devguard.github_client.httpx.patch") as patch_call,
    ):
        client.post_or_update_comment("owner/repo", 3, "hello")
    assert post.called
    assert not patch_call.called
