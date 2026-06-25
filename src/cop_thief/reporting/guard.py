"""SEC-03 Submission Safety Guard — burner-loopback interlock.

Prevents any report from reaching the live Examiner address until production is
explicitly unlocked, while always permitting the burner sandbox address so
formatting/auth can be verified end-to-end first.
"""

from __future__ import annotations

from cop_thief.config import get_config_manager

_BLOCKED_TOKENS = ("segal", "haifa.ac.il")


class SubmissionSafetyException(RuntimeError):
    """Raised when a live submission is attempted while production is locked."""


class SubmissionSafetyGuard:
    """Gate recipient addresses behind the production-locked interlock."""

    def __init__(self, locked: bool | None = None, config_manager=None) -> None:
        """Read the lock state and the always-allowed burner from config."""
        cfg = config_manager or get_config_manager()
        if locked is None:
            locked = cfg.setup.reporting.production_submission_locked
        self._locked = bool(locked)
        self._always_allow = cfg.setup.reporting.burner_email.strip().lower()

    @property
    def locked(self) -> bool:
        """Whether production submission is currently locked."""
        return self._locked

    def verify_safe_recipient(self, email_address: str) -> None:
        """Allow the burner unconditionally; block locked production targets.

        Raises ``SubmissionSafetyException`` if a blocked token appears in the
        address while the production lock is engaged.
        """
        low = email_address.strip().lower()
        if low == self._always_allow:
            return
        if self._locked and any(token in low for token in _BLOCKED_TOKENS):
            raise SubmissionSafetyException(
                "PRODUCTION SUBMISSION LOCKED: Sandbox testing mandatory"
            )
