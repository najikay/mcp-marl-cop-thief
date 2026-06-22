"""StructuredLogger — minimal structured event logging for monitoring.

Events are recorded both to the standard ``logging`` module and to an in-memory
buffer that tests (and a future dashboard) can inspect. Secret-looking keys are
redacted so tokens never leak into logs (PRD §E10).
"""

from __future__ import annotations

import logging

_REDACT_HINTS = ("key", "token", "secret", "password")


class StructuredLogger:
    """Record named events with arbitrary structured fields."""

    def __init__(self, name: str = "cop_thief") -> None:
        self._log = logging.getLogger(name)
        self.events: list[tuple[str, dict]] = []

    def event(self, name: str, **fields: object) -> None:
        """Log a structured event, redacting any secret-looking field values."""
        safe = {k: ("***" if self._is_secret(k) else v) for k, v in fields.items()}
        self.events.append((name, safe))
        self._log.info("%s %s", name, safe)

    @staticmethod
    def _is_secret(key: str) -> bool:
        lowered = key.lower()
        return any(hint in lowered for hint in _REDACT_HINTS)
