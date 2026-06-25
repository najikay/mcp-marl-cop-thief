"""TDD: a barrier is its OWN turn — the Cop walls one adjacent free cell and stays put."""

from __future__ import annotations

from cop_thief.domain.constants import AgentRole
from cop_thief.domain.grid import Grid
from cop_thief.domain.move_language import apply_prose, encode_barrier, parse_intent
from cop_thief.domain.state import DecPomdpGameState


def _state(cop=(2, 2), thief=(4, 4), barriers=frozenset(), left=3) -> DecPomdpGameState:
    return DecPomdpGameState(cop_pos=cop, thief_pos=thief, grid=Grid(shape=(5, 5), barriers=barriers),
                             turn_role=AgentRole.COP, cop_barriers_left=left)


def test_encode_barrier_names_the_walled_direction() -> None:
    """encode_barrier emits a BARRIER intent plus the direction of the walled cell (east here)."""
    prose = encode_barrier(AgentRole.COP, (2, 2), (2, 3))
    assert "[INTENT: BARRIER]" in prose and "east" in prose
    assert parse_intent(prose) == "BARRIER"


def test_intent_tag_cannot_be_spoofed_by_flavor_text() -> None:
    """Only the bracketed prefix sets intent; a later 'barrier' word stays a MOVE."""
    assert parse_intent("[INTENT: MOVE] mind the barrier, edges north") == "MOVE"


def test_barrier_target_must_be_an_adjacent_free_cell() -> None:
    """Legal to wall an adjacent empty cell; illegal to wall own cell, the Thief, or a far cell."""
    state = _state(cop=(2, 2), thief=(2, 1))
    assert state.is_barrier_legal((2, 3)) is True   # adjacent free cell
    assert state.is_barrier_legal((2, 2)) is False  # cannot wall the cell it stands on
    assert state.is_barrier_legal((2, 1)) is False  # cannot wall the Thief's cell
    assert state.is_barrier_legal((4, 4)) is False  # not a King step away


def test_apply_prose_barrier_walls_adjacent_cell_and_cop_stays() -> None:
    """A Cop BARRIER walls the named adjacent cell, the Cop stays put, spends one barrier."""
    walled = apply_prose(_state(cop=(2, 2), left=3), AgentRole.COP, encode_barrier(AgentRole.COP, (2, 2), (2, 3)))
    assert (2, 3) in walled.grid.barriers      # the adjacent cell is now a wall
    assert walled.cop_pos == (2, 2)            # the Cop did NOT move (walling is its own turn)
    assert walled.cop_barriers_left == 2


def test_barrier_is_one_turn_and_not_a_move() -> None:
    """Placing a wall is a SINGLE turn with no move: +1 turn, role flips, −1 barrier, Cop fixed."""
    state = _state(cop=(2, 2), left=3)  # turn_counter 0, turn_role COP
    after = apply_prose(state, AgentRole.COP, encode_barrier(AgentRole.COP, (2, 2), (2, 3)))
    assert after.turn_counter == state.turn_counter + 1   # counts as exactly one turn
    assert after.turn_role is AgentRole.THIEF             # then it's the opponent's turn
    assert after.cop_pos == state.cop_pos                 # the Cop spent the turn walling, not moving
    assert after.cop_barriers_left == state.cop_barriers_left - 1


def test_thief_barrier_is_a_no_op() -> None:
    """The Thief cannot place barriers; a BARRIER prose from it changes nothing."""
    state = DecPomdpGameState(cop_pos=(2, 2), thief_pos=(4, 4), turn_role=AgentRole.THIEF)
    same = apply_prose(state, AgentRole.THIEF, encode_barrier(AgentRole.THIEF, (4, 4), (4, 3)))
    assert same.grid.barriers == frozenset() and same.thief_pos == (4, 4)
