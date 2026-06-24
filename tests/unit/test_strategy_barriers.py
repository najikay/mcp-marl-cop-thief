"""TDD: Cop barrier deployment + the [INTENT: BARRIER] language + trapped-death."""

from __future__ import annotations

from cop_thief.domain.constants import AgentRole, SubGameOutcome
from cop_thief.domain.grid import Grid
from cop_thief.domain.move_language import apply_prose, encode_barrier, parse_intent
from cop_thief.domain.state import DecPomdpGameState
from cop_thief.domain.strategy.heuristic import barrier_target
from cop_thief.sdk.services import MatchCoordinator
from cop_thief.servers.tools.move_tool import resolve_move

_CORNERED_OBS = {"role": "cop", "grid": [5, 5], "cop": [2, 1], "thief": [0, 0],
                 "barriers": [[0, 1], [1, 1]], "barriers_left": 3}


def _cornered() -> DecPomdpGameState:
    """Thief boxed at (0,0) with one escape (1,0); Cop at (2,1) can legally seal it."""
    grid = Grid(shape=(5, 5), barriers=frozenset({(0, 1), (1, 1)}))
    return DecPomdpGameState(cop_pos=(2, 1), thief_pos=(0, 0), grid=grid,
                             turn_role=AgentRole.COP, cop_barriers_left=3)


def test_encode_barrier_and_parse_intent_roundtrip() -> None:
    """encode_barrier emits a BARRIER intent + direction; parse_intent reads the tag."""
    prose = encode_barrier(AgentRole.COP, (2, 1), (1, 0))  # delta (-1,-1) = north-west
    assert "BARRIER" in prose and "north-west" in prose
    assert parse_intent(prose) == "BARRIER"
    assert parse_intent("[INTENT: MOVE] The cop edges north.") == "MOVE"


def test_intent_tag_cannot_be_spoofed_by_flavor_text() -> None:
    """Only the bracketed prefix sets intent; a later 'barrier' word stays a MOVE."""
    assert parse_intent("[INTENT: MOVE] mind the barrier, edges north") == "MOVE"


def test_barrier_target_seals_last_escape() -> None:
    """The Cop's barrier policy seals the Thief's only remaining escape cell."""
    assert barrier_target(_cornered()) == (1, 0)


def test_barrier_target_none_when_thief_far_or_no_budget() -> None:
    """No barrier when the Thief is out of reach or the budget is exhausted."""
    far = DecPomdpGameState(cop_pos=(0, 0), thief_pos=(4, 4), turn_role=AgentRole.COP)
    assert barrier_target(far) is None
    broke = _cornered().model_copy(update={"cop_barriers_left": 0})
    assert barrier_target(broke) is None


def test_resolve_move_cop_deploys_barrier_when_cornering() -> None:
    """request_move returns a BARRIER intent for a Cop that can cut an escape route."""
    assert "[INTENT: BARRIER]" in resolve_move(_CORNERED_OBS)


def test_barrier_deployment_causes_thief_trapped() -> None:
    """Sealing the last escape leaves the Thief with no legal move → THIEF_TRAPPED."""
    sealed = apply_prose(_cornered(), AgentRole.COP, resolve_move(_CORNERED_OBS))
    assert (1, 0) in sealed.grid.barriers
    assert sealed.cop_barriers_left == 2
    assert MatchCoordinator().evaluate_terminal_condition(sealed) is SubGameOutcome.THIEF_TRAPPED
