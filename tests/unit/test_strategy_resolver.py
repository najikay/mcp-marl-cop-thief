"""TDD: the StrategyResolver driving the Angel–Devil minimax planner variants."""

from __future__ import annotations

from cop_thief.domain.constants import AgentRole
from cop_thief.servers.tools.strategy_resolver import StrategyResolver

_FAR = {"role": "cop", "grid": [5, 5], "cop": [0, 0], "thief": [4, 4],
        "barriers": [], "barriers_left": 5}


def test_all_variants_return_legal_treaty_prose() -> None:
    """Every variant planner resolves to a valid treaty transmission."""
    resolver = StrategyResolver()
    for variant in (0, 1, 2):
        assert resolver.resolve({**_FAR, "variant": variant}).startswith("[INTENT:")


def test_resolver_captures_adjacent_thief_via_minimax() -> None:
    """A Cop one step from the Thief plays the capture move (minimax), not a wander."""
    obs = {"role": "cop", "grid": [5, 5], "cop": [2, 2], "thief": [2, 3],
           "barriers": [], "barriers_left": 5, "variant": 0}
    assert StrategyResolver().resolve(obs) == "[INTENT: MOVE] The cop edges east."


def test_label_maps_variant_index() -> None:
    """Variant indices map to the human variant labels for both roles."""
    resolver = StrategyResolver()
    assert resolver.label(AgentRole.COP, 0) == "aggressive"
    assert resolver.label(AgentRole.THIEF, 2) == "defensive"
