"""Strict, immutable Pydantic v2 models for ``config/rate_limits.json``.

Schema mirrors ``PRD_gatekeeper.md``: a versioned document containing per-service
rate/backpressure buckets. ``frozen=True`` guarantees runtime immutability;
``extra="ignore"`` tolerates descriptive ``comment`` keys.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class _Frozen(BaseModel):
    """Base config model: immutable and tolerant of descriptive extra keys."""

    model_config = ConfigDict(frozen=True, extra="ignore")


class ServiceLimit(_Frozen):
    """Rate-limit & backpressure bucket for one external service."""

    requests_per_minute: int
    requests_per_hour: int = 0
    tokens_per_minute: int = 0
    concurrent_max: int
    retry_after_seconds: int
    max_retries: int
    queue_max_depth: int


class RateLimitsInner(_Frozen):
    """Container mapping service name -> its limits."""

    services: dict[str, ServiceLimit]


class RateLimitConfig(_Frozen):
    """Root schema for ``config/rate_limits.json``."""

    version: str
    rate_limits: RateLimitsInner
