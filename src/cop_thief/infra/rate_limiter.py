"""RateLimiter — sliding per-minute window counters per service.

The clock is injectable so tests are deterministic (no real sleeping). This is
the single-concern rate-limit component the gatekeeper composes.
"""

from __future__ import annotations

from collections.abc import Callable

from ..config.rate_limits import RateLimitConfig

_WINDOW_SECONDS = 60.0


class RateLimiter:
    """Allow up to ``requests_per_minute`` calls per service per rolling minute."""

    def __init__(self, config: RateLimitConfig, clock: Callable[[], float]) -> None:
        self._config = config
        self._clock = clock
        self._hits: dict[str, list[float]] = {}

    def allow(self, service: str) -> bool:
        """Record and permit a call if under the per-minute limit, else refuse."""
        limit = self._config.for_service(service).requests_per_minute
        now = self._clock()
        recent = [t for t in self._hits.get(service, []) if now - t < _WINDOW_SECONDS]
        if len(recent) >= limit:
            self._hits[service] = recent
            return False
        recent.append(now)
        self._hits[service] = recent
        return True

    def current_load(self, service: str) -> int:
        """Number of calls counted in the current window for ``service``."""
        now = self._clock()
        return len([t for t in self._hits.get(service, []) if now - t < _WINDOW_SECONDS])
