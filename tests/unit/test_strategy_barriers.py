"""TDD: the §4.3 barrier rule — the Cop walls only its own current cell."""

from __future__ import annotations

from cop_thief.domain.constants import AgentRole
from cop_thief.domain.grid import Grid
from cop_thief.domain.move_language import apply_prose, encode_barrier, parse_intent
from cop_thief.domain.state import DecPomdpGameState


def _state(cop=(2, 2), thief=(4, 4), barriers=frozenset(), left=3) -> DecPomdpGameState:
    return DecPomdpGameState(cop_pos=cop, thief_pos=thief, grid=Grid(shape=(5, 5), barriers=barriers),
                             turn_role=AgentRole.COP, cop_barriers_left=left)


def test_encode_barrier_targets_own_cell() -> None:
    """encode_barrier emits a BARRIER intent for the Cop's own cell (no direction)."""
    prose = encode_barrier(AgentRole.COP)
    assert "[INTENT: BARRIER]" in prose and "stands on" in prose
    assert parse_intent(prose) == "BARRIER"


def test_intent_tag_cannot_be_spoofed_by_flavor_text() -> None:
    """Only the bracketed prefix sets intent; a later 'barrier' word stays a MOVE."""
    assert parse_intent("[INTENT: MOVE] mind the barrier, edges north") == "MOVE"


def test_barrier_legal_only_on_current_cell() -> None:
    """§4.3: the Cop may wall only the cell it stands on — adjacent/far are illegal."""
    state = _state(cop=(2, 2))
    assert state.is_barrier_legal((2, 2)) is True
    assert state.is_barrier_legal((2, 3)) is False  # adjacent is NOT allowed
    assert state.is_barrier_legal((4, 4)) is False


def test_apply_prose_barrier_walls_current_cell() -> None:
    """A Cop BARRIER seals its current cell, spends one barrier, and does not move."""
    walled = apply_prose(_state(cop=(2, 2), left=3), AgentRole.COP, encode_barrier(AgentRole.COP))
    assert (2, 2) in walled.grid.barriers
    assert walled.cop_barriers_left == 2
    assert walled.cop_pos == (2, 2)


def test_thief_barrier_is_a_no_op() -> None:
    """The Thief cannot place barriers (§4.3); a BARRIER prose from it changes nothing."""
    state = DecPomdpGameState(cop_pos=(2, 2), thief_pos=(4, 4), turn_role=AgentRole.THIEF)
    same = apply_prose(state, AgentRole.THIEF, encode_barrier(AgentRole.THIEF))
    assert same.grid.barriers == frozenset()
