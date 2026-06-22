"""Typed, versioned models for the API-gatekeeper rate limits.

Loaded from ``config/rate_limits.json`` so no limit is ever hardcoded in the
gatekeeper itself (PRD §E6 / PLAN §5).
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from .. import __version__

_DEFAULT_PATH = Path(__file__).resolve().parents[3] / "config" / "rate_limits.json"


@dataclass(frozen=True)
class ServiceLimit:
    """Per-service limits for one external dependency (llm, gmail, default)."""

    requests_per_minute: int
    concurrent_max: int
    retry_after_seconds: int
    max_retries: int
    queue_max_depth: int

    @classmethod
    def from_dict(cls, data: dict) -> ServiceLimit:
        """Build a limit, rejecting non-positive values where they make no sense."""
        limit = cls(
            requests_per_minute=int(data["requests_per_minute"]),
            concurrent_max=int(data["concurrent_max"]),
            retry_after_seconds=int(data["retry_after_seconds"]),
            max_retries=int(data["max_retries"]),
            queue_max_depth=int(data["queue_max_depth"]),
        )
        if limit.requests_per_minute < 1 or limit.queue_max_depth < 0:
            raise ValueError(f"invalid rate-limit values: {data}")
        return limit


@dataclass(frozen=True)
class RateLimitConfig:
    """All service limits, with a ``default`` fallback for unknown services."""

    version: str
    services: dict[str, ServiceLimit]

    def for_service(self, service: str) -> ServiceLimit:
        """Return the limit for ``service``, falling back to ``default``."""
        return self.services.get(service, self.services["default"])

    @classmethod
    def from_dict(cls, data: dict) -> RateLimitConfig:
        """Validate and construct from raw JSON; ``default`` is mandatory."""
        services = {k: ServiceLimit.from_dict(v) for k, v in data["services"].items()}
        if "default" not in services:
            raise ValueError("rate_limits must define a 'default' service")
        return cls(version=str(data.get("version", __version__)), services=services)


def load_rate_limits(path: str | Path | None = None) -> RateLimitConfig:
    """Read and validate the rate-limit config file."""
    target = Path(path) if path is not None else _DEFAULT_PATH
    if not target.exists():
        raise FileNotFoundError(f"rate-limit config not found: {target}")
    raw = json.loads(target.read_text(encoding="utf-8"))
    return RateLimitConfig.from_dict(raw)
