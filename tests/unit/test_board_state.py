"""Unit tests for BoardState and the transition function P."""

from __future__ import annotations

import random

from cop_thief.constants import AgentRole, Direction
from cop_thief.domain.action import Action
from cop_thief.domain.board_state import BoardState, BoardStateMachine
from cop_thief.domain.grid import Cell, Grid


def _machine(max_barriers: int = 5) -> BoardStateMachine:
    return BoardStateMachine(Grid(5, 5), max_barriers)


def test_initial_state_distinct_and_reproducible():
    machine = _machine()
    a = machine.initial_state(True, random.Random(1))
    b = machine.initial_state(True, random.Random(1))
    assert a.cop != a.thief
    assert (a.cop, a.thief) == (b.cop, b.thief)  # same seed -> same start


def test_move_increments_count_and_position():
    machine = _machine()
    state = BoardState(cop=Cell(2, 2), thief=Cell(0, 0), barriers_left=5)
    nxt = machine.apply(state, Action.move(AgentRole.COP, Direction.NW))
    assert nxt.cop == Cell(1, 1)
    assert nxt.move_count == 1


def test_move_into_wall_is_clamped():
    machine = _machine()
    state = BoardState(cop=Cell(0, 0), thief=Cell(4, 4), barriers_left=5)
    nxt = machine.apply(state, Action.move(AgentRole.COP, Direction.N))
    assert nxt.cop == Cell(0, 0)  # clamped to stay


def test_move_into_barrier_is_clamped():
    machine = _machine()
    state = BoardState(
        cop=Cell(2, 2), thief=Cell(4, 4), barriers=frozenset({Cell(2, 3)}), barriers_left=5
    )
    nxt = machine.apply(state, Action.move(AgentRole.COP, Direction.E))
    assert nxt.cop == Cell(2, 2)


def test_place_barrier_seals_cell_and_decrements_quota():
    machine = _machine()
    state = BoardState(cop=Cell(1, 1), thief=Cell(4, 4), barriers_left=5)
    nxt = machine.apply(state, Action.barrier(AgentRole.COP))
    assert Cell(1, 1) in nxt.barriers
    assert nxt.barriers_left == 4


def test_strategic_start_uses_corners():
    machine = _machine()
    state = machine.initial_state(False, random.Random(0))
    assert state.cop == Cell(0, 0)
    assert state.thief == Cell(4, 4)
