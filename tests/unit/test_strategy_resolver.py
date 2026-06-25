"""TDD: the StrategyResolver driving the Angel–Devil minimax planner variants."""

from __future__ import annotations

from cop_thief.domain.constants import ActionType, AgentRole
from cop_thief.domain.state import DecPomdpGameState
from cop_thief.domain.strategy.minimax import MinimaxPlanner
from cop_thief.servers.tools.strategy_resolver import StrategyResolver

_FAR = {"role": "cop", "grid": [5, 5], "cop": [0, 0], "thief": [4, 4],
        "barriers": [], "barriers_left": 5, "turn": 0}


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


def test_resolve_tolerates_a_string_variant_label() -> None:
    """An opponent's non-numeric variant (e.g. 'standard') must not crash — falls back safely."""
    for variant in ("standard", "aggressive", None, "99", 7):
        prose = StrategyResolver().resolve({**_FAR, "variant": variant})
        assert prose.startswith("[INTENT:")


def test_label_maps_variant_index() -> None:
    """Variant indices map to the human variant labels for both roles."""
    resolver = StrategyResolver()
    assert resolver.label(AgentRole.COP, 0) == "aggressive"
    assert resolver.label(AgentRole.THIEF, 2) == "defensive"


def test_deterministic_mode_is_a_pure_function_of_the_observation() -> None:
    """Tournament mode: same observation → same move, regardless of variant or call history (K3)."""
    resolver = StrategyResolver(deterministic=True)
    first = resolver.resolve(_FAR)
    assert resolver.resolve(_FAR) == first                       # no history dependence
    assert resolver.resolve({**_FAR, "variant": 2}) == first     # variant ignored in tournament mode


def test_barriers_disabled_removes_barrier_actions() -> None:
    """With barriers OFF, the planner offers no barrier actions (per a barriers-off agreement)."""
    state = DecPomdpGameState(cop_pos=(2, 2), thief_pos=(4, 4), turn_role=AgentRole.COP, cop_barriers_left=3)
    acts = MinimaxPlanner(barriers=False).actions(state, AgentRole.COP)
    assert all(a[0] is not ActionType.PLACE_BARRIER for a in acts)
