"""Aggregated configuration schemas.

Re-exports the root models (kept in dedicated modules to respect the 150-line
limit, Guidelines §3.2) and defines :class:`LoggingConfig` for
``config/logging_config.json``. The logging schema is intentionally permissive
(``extra="allow"``) because it is a ``logging.config.dictConfig`` payload whose
exact keys are owned by the stdlib.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict

from cop_thief.config.rate_limit_models import (
    RateLimitConfig,
    RateLimitsInner,
    ServiceLimit,
)
from cop_thief.config.setup_models import (
    GameConfig,
    LLMEndpoint,
    LLMRouting,
    RLConfig,
    ScoringConfig,
    ServerConfig,
    SetupConfig,
    TokenBudget,
)


class LoggingConfig(BaseModel):
    """Validated wrapper around a ``logging.config.dictConfig`` dictionary.

    Only ``version`` is strictly required; all other dictConfig keys are
    preserved verbatim (``extra="allow"``) so the raw mapping can be handed to
    :func:`logging.config.dictConfig` unchanged.
    """

    model_config = ConfigDict(frozen=True, extra="allow")

    version: int

    def as_dict_config(self) -> dict:
        """Return the full dictConfig mapping (including preserved extras)."""
        return self.model_dump()


__all__ = [
    "SetupConfig",
    "RateLimitConfig",
    "LoggingConfig",
    "GameConfig",
    "ScoringConfig",
    "ServerConfig",
    "LLMEndpoint",
    "LLMRouting",
    "RLConfig",
    "TokenBudget",
    "RateLimitsInner",
    "ServiceLimit",
]
