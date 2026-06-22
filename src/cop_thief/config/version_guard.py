"""Single-concern configuration version verification.

This module isolates one responsibility: asserting that a configuration file's
declared version matches the version the running code expects (Guidelines §8.1).
It is exposed as a mixin so any config consumer can inherit the check without
duplicating logic (DRY).
"""

from __future__ import annotations


class ConfigurationVersionError(RuntimeError):
    """Raised when a config file's version does not match the expected version."""


class VersionGuardMixin:
    """Mixin providing a single, independently testable version check."""

    @staticmethod
    def verify_config_version(expected: str, actual: str) -> None:
        """Verify ``actual`` config version equals ``expected``.

        Why: a config file written for a different code version may carry
        incompatible keys/semantics; failing fast at load time prevents silent
        misconfiguration during a game run.

        Args:
            expected: Version string the running code requires (e.g. ``"1.00"``).
            actual: Version string declared inside the loaded config file.

        Raises:
            ConfigurationVersionError: If ``actual`` differs from ``expected``.
        """
        if actual != expected:
            raise ConfigurationVersionError(
                f"Config version mismatch: expected '{expected}', got '{actual}'."
            )
