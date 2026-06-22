"""Unit tests for the sliding-window RateLimiter."""

from __future__ import annotations

from cop_thief.config.rate_limits import RateLimitConfig
from cop_thief.infra.rate_limiter import RateLimiter


def _config(rpm: int) -> RateLimitConfig:
    svc = {
        "requests_per_minute": rpm,
        "concurrent_max": 1,
        "retry_after_seconds": 1,
        "max_retries": 1,
        "queue_max_depth": 5,
    }
    return RateLimitConfig.from_dict({"version": "1.0.0", "services": {"default": svc}})


class _Clock:
    def __init__(self) -> None:
        self.now = 0.0

    def __call__(self) -> float:
        return self.now


def test_allows_under_limit():
    limiter = RateLimiter(_config(3), _Clock())
    assert all(limiter.allow("default") for _ in range(3))


def test_blocks_at_limit():
    limiter = RateLimiter(_config(2), _Clock())
    limiter.allow("default")
    limiter.allow("default")
    assert not limiter.allow("default")


def test_window_reset_re_allows():
    clock = _Clock()
    limiter = RateLimiter(_config(1), clock)
    assert limiter.allow("default")
    assert not limiter.allow("default")
    clock.now = 61.0  # next minute
    assert limiter.allow("default")


def test_unknown_service_uses_default():
    limiter = RateLimiter(_config(1), _Clock())
    assert limiter.allow("llm")  # falls back to default
    assert not limiter.allow("llm")
