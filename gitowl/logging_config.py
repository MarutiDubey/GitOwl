"""Centralised logging setup for GitOwl."""

from __future__ import annotations

import logging
import os

_CONFIGURED = False


def setup_logging(level: str | None = None) -> None:
    """Configure the root logger once, honouring LOG_LEVEL from the environment."""
    global _CONFIGURED
    if _CONFIGURED:
        return

    resolved = (level or os.getenv("LOG_LEVEL") or "INFO").upper()
    logging.basicConfig(
        level=getattr(logging, resolved, logging.INFO),
        format="%(asctime)s %(levelname)-7s %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )
    _CONFIGURED = True


def get_logger(name: str) -> logging.Logger:
    """Return a namespaced logger, ensuring logging is configured first."""
    setup_logging()
    return logging.getLogger(name)
