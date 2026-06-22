"""Configuration subsystem: typed, immutable, version-guarded runtime config."""

from cop_thief.config.manager import (
    EXPECTED_VERSION,
    ConfigManager,
    get_config_manager,
)
from cop_thief.config.models import (
    LoggingConfig,
    RateLimitConfig,
    SetupConfig,
)
from cop_thief.config.version_guard import (
    ConfigurationVersionError,
    VersionGuardMixin,
)

__all__ = [
    "ConfigManager",
    "get_config_manager",
    "EXPECTED_VERSION",
    "ConfigurationVersionError",
    "VersionGuardMixin",
    "SetupConfig",
    "RateLimitConfig",
    "LoggingConfig",
]
