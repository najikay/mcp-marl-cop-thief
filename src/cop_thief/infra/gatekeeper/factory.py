"""Shared default-construction for the API gatekeeper (DRY helper).

Centralises the wiring of config -> token tracker -> gatekeeper so every
consumer (encoder, parser, future orchestrator) builds it identically.
"""

from __future__ import annotations

from cop_thief.config import get_config_manager
from cop_thief.infra.gatekeeper.engine import ApiGatekeeper
from cop_thief.infra.gatekeeper.token_tracker import TokenTracker


def build_default_gatekeeper() -> ApiGatekeeper:
    """Construct an ApiGatekeeper from the active configuration."""
    cfg = get_config_manager()
    tracker = TokenTracker(
        usage_file=cfg.setup.token_budget.usage_file, config_manager=cfg
    )
    return ApiGatekeeper(cfg.rate_limits, cfg.setup.llm_routing, token_tracker=tracker)
