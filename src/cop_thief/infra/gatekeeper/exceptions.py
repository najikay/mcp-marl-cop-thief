"""Custom exceptions raised by the API Gatekeeper.

Dedicated exception types let callers (notably the Orchestrator) react
precisely — e.g. catching ``BackpressureOverflowError`` to slow the game tick
rather than crashing.
"""

from __future__ import annotations


class RateLimitExceededError(RuntimeError):
    """Raised when a service's configured rate window is exhausted."""


class ProviderUpstreamError(RuntimeError):
    """Raised when every LLM provider (primary and fallback) has failed."""


class BackpressureOverflowError(RuntimeError):
    """Raised when the FIFO queue is full; signals the caller to slow down."""
