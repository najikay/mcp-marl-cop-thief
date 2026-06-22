"""Custom exceptions raised by the SDK business facade."""

from __future__ import annotations


class SdkInitializationError(RuntimeError):
    """Raised when the SDK cannot wire its config/gatekeeper/coordinator."""


class IllegalGameMutationError(RuntimeError):
    """Raised when a caller attempts an invalid or non-immutable state change."""


class AdversarialHijackDetectedError(RuntimeError):
    """Raised when an inbound message carries a prompt-injection signature."""
