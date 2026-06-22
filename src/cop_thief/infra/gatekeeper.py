"""ApiGatekeeper — the single chokepoint for every external call.

All LLM and Gmail calls must go through :meth:`execute`. It applies the
per-service rate limit (raising :class:`BackpressureError` when over budget —
never crashing), wraps the call in the retry policy, and logs every attempt for
monitoring (PRD §E4, PLAN §5).
"""

from __future__ import annotations

import time
from collections.abc import Callable
from typing import TypeVar

from ..config.rate_limits import RateLimitConfig, load_rate_limits
from .errors import BackpressureError
from .logger import StructuredLogger
from .rate_limiter import RateLimiter
from .retry import RetryPolicy

T = TypeVar("T")


class ApiGatekeeper:
    """Rate-limit, retry and log all external dependency calls."""

    def __init__(
        self,
        config: RateLimitConfig | None = None,
        logger: StructuredLogger | None = None,
        clock: Callable[[], float] = time.monotonic,
        sleeper: Callable[[float], None] = time.sleep,
    ) -> None:
        self._config = config or load_rate_limits()
        self._logger = logger or StructuredLogger()
        self._sleeper = sleeper
        self._limiter = RateLimiter(self._config, clock)

    def execute(self, service: str, func: Callable[[], T]) -> T:
        """Run ``func`` for ``service`` under rate limiting + retry, logging it."""
        if not self._limiter.allow(service):
            self._logger.event("gatekeeper.backpressure", service=service)
            raise BackpressureError(f"{service} rate limit reached; retry later")
        limit = self._config.for_service(service)
        policy = RetryPolicy(limit.max_retries, limit.retry_after_seconds, self._sleeper)
        self._logger.event("gatekeeper.execute", service=service)
        return policy.run(func)

    @property
    def logger(self) -> StructuredLogger:
        """Expose the logger so callers can inspect recorded events."""
        return self._logger
