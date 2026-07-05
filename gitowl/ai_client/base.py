"""Base interface every AI provider must implement."""

from __future__ import annotations

import abc

from gitowl.config import AIConfig
from gitowl.models import Finding, PrDescription, ReviewResult


class AIProviderError(RuntimeError):
    """Raised when an AI provider fails to produce a usable review."""


class AIProvider(abc.ABC):
    """Contract for the review-reasoning layer.

    Implementations translate a diff + static-analysis findings into a
    structured :class:`~gitowl.models.ReviewResult`.
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

    def describe(self, diff: str) -> PrDescription:
        """Generate a PR description for ``diff``.

        Optional capability: providers that talk to a real chat API implement
        this. Others (e.g. the offline eval mock) inherit this default, which
        signals the feature is unsupported.
        """
        raise AIProviderError(f"Provider '{self.name}' does not support describe.")
