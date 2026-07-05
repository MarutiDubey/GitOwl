"""Minimal GitHub REST client for fetching PR diffs and posting comments."""

from __future__ import annotations

import httpx

from gitowl.comment import COMMENT_MARKER
from gitowl.logging_config import get_logger
from gitowl.suggest import InlineSuggestion

logger = get_logger(__name__)

_API_ROOT = "https://api.github.com"
_TIMEOUT = 30.0


class GitHubError(RuntimeError):
    """Raised on GitHub API failures."""


class GitHubClient:
    """Thin wrapper over the subset of the GitHub API GitOwl needs."""

    def __init__(self, token: str, api_root: str = _API_ROOT) -> None:
        if not token:
            raise GitHubError("A GitHub token is required (set GITHUB_TOKEN).")
        self._token = token
        self._api_root = api_root.rstrip("/")

    def _headers(self, accept: str = "application/vnd.github+json") -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self._token}",
            "Accept": accept,
            "X-GitHub-Api-Version": "2022-11-28",
        }

    def fetch_pr_diff(self, repo: str, pr_number: int) -> str:
        """Fetch the unified diff for ``owner/repo`` PR ``pr_number``."""
        url = f"{self._api_root}/repos/{repo}/pulls/{pr_number}"
        try:
            resp = httpx.get(
                url,
                headers=self._headers("application/vnd.github.v3.diff"),
                timeout=_TIMEOUT,
                follow_redirects=True,
            )
            resp.raise_for_status()
        except httpx.HTTPError as exc:
            raise GitHubError(f"failed to fetch PR diff: {exc}") from exc
        return resp.text

    def fetch_pr_body(self, repo: str, pr_number: int) -> str:
        """Return the current body (description) of ``owner/repo`` PR ``pr_number``."""
        url = f"{self._api_root}/repos/{repo}/pulls/{pr_number}"
        try:
            resp = httpx.get(url, headers=self._headers(), timeout=_TIMEOUT)
            resp.raise_for_status()
        except httpx.HTTPError as exc:
            raise GitHubError(f"failed to fetch PR body: {exc}") from exc
        return resp.json().get("body") or ""

    def update_pr_body(self, repo: str, pr_number: int, body: str) -> None:
        """Set the body (description) of ``owner/repo`` PR ``pr_number``."""
        url = f"{self._api_root}/repos/{repo}/pulls/{pr_number}"
        try:
            resp = httpx.patch(url, headers=self._headers(), json={"body": body}, timeout=_TIMEOUT)
            resp.raise_for_status()
        except httpx.HTTPError as exc:
            raise GitHubError(f"failed to update PR body: {exc}") from exc
        logger.info("Updated PR description on %s#%d", repo, pr_number)

    def post_review_comments(
        self, repo: str, pr_number: int, suggestions: list[InlineSuggestion]
    ) -> int:
        """Post ``suggestions`` as inline comments on a single PR review.

        Returns the number posted. An empty list is a no-op (returns 0). The
        comments go out as one ``event: COMMENT`` review so they land together
        without approving or requesting changes.
        """
        if not suggestions:
            return 0
        url = f"{self._api_root}/repos/{repo}/pulls/{pr_number}/reviews"
        payload = {
            "event": "COMMENT",
            "comments": [
                {"path": s.path, "line": s.line, "side": "RIGHT", "body": s.body}
                for s in suggestions
            ],
        }
        try:
            resp = httpx.post(url, headers=self._headers(), json=payload, timeout=_TIMEOUT)
            resp.raise_for_status()
        except httpx.HTTPError as exc:
            raise GitHubError(f"failed to post review suggestions: {exc}") from exc
        logger.info("Posted %d inline suggestion(s) to %s#%d", len(suggestions), repo, pr_number)
        return len(suggestions)

    def _existing_comment_id(self, repo: str, pr_number: int) -> int | None:
        """Find GitOwl's previous comment on this PR, if any."""
        url = f"{self._api_root}/repos/{repo}/issues/{pr_number}/comments"
        try:
            resp = httpx.get(url, headers=self._headers(), timeout=_TIMEOUT)
            resp.raise_for_status()
        except httpx.HTTPError as exc:
            logger.warning("Could not list PR comments: %s", exc)
            return None
        for comment in resp.json():
            if COMMENT_MARKER in comment.get("body", ""):
                return comment["id"]
        return None

    def post_or_update_comment(self, repo: str, pr_number: int, body: str) -> None:
        """Post a new review comment, or update GitOwl's existing one."""
        existing = self._existing_comment_id(repo, pr_number)
        try:
            if existing is not None:
                url = f"{self._api_root}/repos/{repo}/issues/comments/{existing}"
                resp = httpx.patch(
                    url, headers=self._headers(), json={"body": body}, timeout=_TIMEOUT
                )
            else:
                url = f"{self._api_root}/repos/{repo}/issues/{pr_number}/comments"
                resp = httpx.post(
                    url, headers=self._headers(), json={"body": body}, timeout=_TIMEOUT
                )
            resp.raise_for_status()
        except httpx.HTTPError as exc:
            raise GitHubError(f"failed to post PR comment: {exc}") from exc
        logger.info("Posted GitOwl review to %s#%d", repo, pr_number)
