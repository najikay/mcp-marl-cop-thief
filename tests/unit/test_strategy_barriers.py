"""TDD: the §4.3 barrier-move — the Cop walls the cell it vacates and steps off."""

from __future__ import annotations

from cop_thief.domain.constants import AgentRole
from cop_thief.domain.grid import Grid
from cop_thief.domain.move_language import apply_prose, encode_barrier, parse_intent
from cop_thief.domain.state import DecPomdpGameState


def _state(cop=(2, 2), thief=(4, 4), barriers=frozenset(), left=3) -> DecPomdpGameState:
    return DecPomdpGameState(cop_pos=cop, thief_pos=thief, grid=Grid(shape=(5, 5), barriers=barriers),
                             turn_role=AgentRole.COP, cop_barriers_left=left)


def test_encode_barrier_names_the_step_direction() -> None:
    """encode_barrier emits a BARRIER intent plus the step direction (east here)."""
    prose = encode_barrier(AgentRole.COP, (2, 2), (2, 3))
    assert "[INTENT: BARRIER]" in prose and "steps east" in prose
    assert parse_intent(prose) == "BARRIER"


def test_intent_tag_cannot_be_spoofed_by_flavor_text() -> None:
    """Only the bracketed prefix sets intent; a later 'barrier' word stays a MOVE."""
    assert parse_intent("[INTENT: MOVE] mind the barrier, edges north") == "MOVE"


def test_barrier_move_requires_a_distinct_legal_step() -> None:
    """§4.3: legal to an adjacent free cell; illegal to stay-put or a far cell (no one stands on a wall)."""
    state = _state(cop=(2, 2))
    assert state.is_barrier_legal((2, 3)) is True   # adjacent step
    assert state.is_barrier_legal((2, 2)) is False  # cannot wall and stay on it
    assert state.is_barrier_legal((4, 4)) is False  # not a King step


def test_apply_prose_barrier_walls_vacated_cell_and_steps_off() -> None:
    """A Cop BARRIER walls the cell it leaves, steps to the named cell, spends one barrier."""
    walled = apply_prose(_state(cop=(2, 2), left=3), AgentRole.COP, encode_barrier(AgentRole.COP, (2, 2), (2, 3)))
    assert (2, 2) in walled.grid.barriers      # the vacated cell is now a wall
    assert walled.cop_pos == (2, 3)            # the Cop stepped off it (never stands on a barrier)
    assert walled.cop_barriers_left == 2


def test_barrier_move_is_one_turn() -> None:
    """The whole barrier-move (wall + step) is a SINGLE turn: +1 move, role flips, −1 barrier."""
    state = _state(cop=(2, 2), left=3)  # turn_counter 0, turn_role COP
    after = apply_prose(state, AgentRole.COP, encode_barrier(AgentRole.COP, (2, 2), (2, 3)))
    assert after.turn_counter == state.turn_counter + 1   # counts as exactly one move
    assert after.turn_role is AgentRole.THIEF             # then it's the opponent's turn
    assert after.cop_barriers_left == state.cop_barriers_left - 1


def test_thief_barrier_is_a_no_op() -> None:
    """The Thief cannot place barriers (§4.3); a BARRIER prose from it changes nothing."""
    state = DecPomdpGameState(cop_pos=(2, 2), thief_pos=(4, 4), turn_role=AgentRole.THIEF)
    same = apply_prose(state, AgentRole.THIEF, encode_barrier(AgentRole.THIEF, (4, 4), (4, 3)))
    assert same.grid.barriers == frozenset() and same.thief_pos == (4, 4)
