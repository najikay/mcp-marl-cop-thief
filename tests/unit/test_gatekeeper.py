"""Unit tests for the ApiGatekeeper chokepoint."""

from __future__ import annotations

import pytest

from cop_thief.config.rate_limits import RateLimitConfig
from cop_thief.infra.errors import BackpressureError, TransientError
from cop_thief.infra.gatekeeper import ApiGatekeeper


def _config(rpm: int, max_retries: int = 2) -> RateLimitConfig:
    svc = {
        "requests_per_minute": rpm,
        "concurrent_max": 1,
        "retry_after_seconds": 0,
        "max_retries": max_retries,
        "queue_max_depth": 5,
    }
    return RateLimitConfig.from_dict({"version": "1.0.0", "services": {"default": svc}})


def _gatekeeper(config: RateLimitConfig) -> ApiGatekeeper:
    return ApiGatekeeper(config=config, clock=lambda: 0.0, sleeper=lambda _s: None)


def test_call_passes_through_and_is_logged():
    gk = _gatekeeper(_config(5))
    assert gk.execute("default", lambda: "result") == "result"
    assert any(name == "gatekeeper.execute" for name, _ in gk.logger.events)


def test_rate_limited_call_raises_backpressure():
    gk = _gatekeeper(_config(1))
    gk.execute("default", lambda: "ok")
    with pytest.raises(BackpressureError):
        gk.execute("default", lambda: "ok")
    assert any(name == "gatekeeper.backpressure" for name, _ in gk.logger.events)


def test_transient_failure_is_retried():
    gk = _gatekeeper(_config(5, max_retries=3))
    calls = {"n": 0}

    def flaky():
        calls["n"] += 1
        if calls["n"] < 2:
            raise TransientError("temporary")
        return "ok"

    assert gk.execute("default", flaky) == "ok"


def test_uses_default_rate_limits_file():
    gk = ApiGatekeeper(clock=lambda: 0.0, sleeper=lambda _s: None)
    assert gk.execute("llm", lambda: 1) == 1
