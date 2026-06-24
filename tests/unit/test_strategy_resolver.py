"""TDD: the stateful StrategyResolver (roster variants + Q-policy in live play)."""

from __future__ import annotations

import random

from cop_thief.domain.constants import AgentRole
from cop_thief.servers.tools.move_tool import resolve_move
from cop_thief.servers.tools.strategy_resolver import StrategyResolver

_FAR = {"role": "cop", "grid": [5, 5], "cop": [0, 0], "thief": [4, 4],
        "barriers": [], "barriers_left": 5}


def test_variant0_cold_q_matches_deterministic_geometry() -> None:
    """Variant 0 (epsilon 0, cold Q) falls back to geometry → identical to resolve_move."""
    assert StrategyResolver().resolve(_FAR) == resolve_move(_FAR)


def test_all_variants_return_legal_treaty_prose() -> None:
    """Every roster variant resolves to a valid treaty transmission."""
    random.seed(7)
    resolver = StrategyResolver()
    for variant in (0, 1, 2):
        assert resolver.resolve({**_FAR, "variant": variant}).startswith("[INTENT:")


def test_rosters_persist_across_calls() -> None:
    """The same variant agent object is reused across calls (state persists)."""
    resolver = StrategyResolver()
    first = resolver._rosters[AgentRole.COP].agent(1)
    resolver.resolve({**_FAR, "variant": 1})
    assert resolver._rosters[AgentRole.COP].agent(1) is first


def test_label_maps_variant_index() -> None:
    """Variant indices map to the human roster labels for both roles."""
    resolver = StrategyResolver()
    assert resolver.label(AgentRole.COP, 0) == "aggressive"
    assert resolver.label(AgentRole.THIEF, 2) == "defensive"
