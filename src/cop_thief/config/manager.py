"""Centralized, validated, version-guarded configuration loader.

``ConfigManager`` is the single source of truth for runtime configuration: it
loads the JSON files via :mod:`pathlib`, validates them through the strict
Pydantic models, and enforces version compatibility (Guidelines §7.3/§8.1).
``get_config_manager`` provides a process-wide cached (effectively singleton)
instance via :func:`functools.lru_cache`.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from cop_thief.config.env_loader import load_env_once
from cop_thief.config.models import LoggingConfig, RateLimitConfig, SetupConfig
from cop_thief.config.version_guard import VersionGuardMixin

EXPECTED_VERSION = "1.00"
_PROJECT_ROOT = Path(__file__).resolve().parents[3]
_DEFAULT_CONFIG_DIR = _PROJECT_ROOT / "config"


class ConfigManager(VersionGuardMixin):
    """Load, validate and version-check all configuration files."""

    def __init__(self, config_dir: Path | None = None) -> None:
        """Initialise and eagerly load every config file.

        Args:
            config_dir: Directory holding the JSON config files. Defaults to the
                project-root ``config/`` directory.
        """
        load_env_once()  # populate os.environ from .env before anything reads secrets
        self._dir = Path(config_dir) if config_dir else _DEFAULT_CONFIG_DIR
        self._setup = self._load_setup()
        self._rate_limits = self._load_rate_limits()
        self._logging = self._load_logging()

    def _read(self, name: str) -> dict:
        """Read and parse a JSON config file by name (relative paths only)."""
        with (self._dir / name).open(encoding="utf-8") as handle:
            return json.load(handle)

    def _load_setup(self) -> SetupConfig:
        """Validate ``setup.json`` and assert its version matches the code."""
        cfg = SetupConfig(**self._read("setup.json"))
        self.verify_config_version(EXPECTED_VERSION, cfg.version)
        return cfg

    def _load_rate_limits(self) -> RateLimitConfig:
        """Validate ``rate_limits.json`` and assert its version matches."""
        cfg = RateLimitConfig(**self._read("rate_limits.json"))
        self.verify_config_version(EXPECTED_VERSION, cfg.version)
        return cfg

    def _load_logging(self) -> LoggingConfig:
        """Validate ``logging_config.json`` (stdlib dictConfig payload)."""
        return LoggingConfig(**self._read("logging_config.json"))

    @property
    def setup(self) -> SetupConfig:
        """Immutable game/runtime configuration."""
        return self._setup

    def get_setup(self) -> SetupConfig:
        """Return the validated setup configuration (method-style accessor)."""
        return self._setup

    @property
    def rate_limits(self) -> RateLimitConfig:
        """Immutable API gatekeeper rate-limit configuration."""
        return self._rate_limits

    @property
    def logging(self) -> LoggingConfig:
        """Validated logging dictConfig wrapper."""
        return self._logging

    @property
    def economics(self) -> dict:
        """Per-provider USD pricing ledger (validated via SetupConfig)."""
        return self._setup.economics


@lru_cache(maxsize=1)
def get_config_manager() -> ConfigManager:
    """Return the process-wide cached ``ConfigManager`` (lazy singleton)."""
    return ConfigManager()
