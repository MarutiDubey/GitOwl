"""Base interface every AI provider must implement."""

from __future__ import annotations

import abc

from devguard.config import AIConfig
from devguard.models import Finding, ReviewResult


class AIProviderError(RuntimeError):
    """Raised when an AI provider fails to produce a usable review."""


class AIProvider(abc.ABC):
    """Contract for the review-reasoning layer.

    Implementations translate a diff + static-analysis findings into a
    structured :class:`~devguard.models.ReviewResult`.
    """

    #: Registry key, e.g. "openrouter". Set on each subclass.
    name: str = ""

    def __init__(self, config: AIConfig) -> None:
        self.config = config

    @abc.abstractmethod
    def review(self, diff: str, findings: list[Finding]) -> ReviewResult:
        """Analyse ``diff`` (optionally aided by Semgrep ``findings``).

        Returns a structured review. Should raise :class:`AIProviderError`
        on unrecoverable failures (network, auth, malformed model output).
        """
        raise NotImplementedError
