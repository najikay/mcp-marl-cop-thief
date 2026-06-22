"""Controlled error types for the gatekeeper.

Distinguishing transient from permanent failures lets the retry policy know what
is worth retrying; :class:`BackpressureError` is a *signal*, not a crash — the
caller should slow down and retry later (PRD §E4: never crash on overflow).
"""

from __future__ import annotations


class TransientError(Exception):
    """A temporary failure (timeout, 5xx) that is safe to retry."""


class PermanentError(Exception):
    """A non-retryable failure (bad request, auth) that must surface at once."""


class BackpressureError(Exception):
    """Raised when a service is rate-limited or its queue is full."""
