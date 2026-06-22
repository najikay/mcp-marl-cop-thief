"""Custom exceptions for the orchestrator subsystem."""

from __future__ import annotations


class NaturalLanguageTranslationError(RuntimeError):
    """Raised when state->prose encoding fails or returns empty output."""


class BeliefDesynchronizationError(RuntimeError):
    """Raised when parsed beliefs irreconcilably conflict with known state."""


class AdversarialGrudgeTriggeredError(RuntimeError):
    """Signals that a rival group has tripped the tit-for-tat grudge."""
