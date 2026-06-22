"""Unit tests for the rule mixins and composed RulesEngine."""

from __future__ import annotations

from cop_thief.constants import AgentRole, Direction, SubGameOutcome
from cop_thief.domain.action import Action
from cop_thief.domain.board_state import BoardState
from cop_thief.domain.grid import Cell, Grid
from cop_thief.domain.rules import RulesEngine


def _engine(max_moves: int = 25) -> RulesEngine:
    return RulesEngine(Grid(5, 5), max_moves)


def test_legal_and_illegal_moves():
    engine = _engine()
    state = BoardState(cop=Cell(0, 0), thief=Cell(4, 4), barriers_left=5)
    assert engine.validate(state, Action.move(AgentRole.COP, Direction.SE))
    assert not engine.validate(state, Action.move(AgentRole.COP, Direction.N))


def test_thief_cannot_place_barrier():
    engine = _engine()
    state = BoardState(cop=Cell(0, 0), thief=Cell(4, 4), barriers_left=5)
    assert not engine.validate(state, Action.barrier(AgentRole.THIEF))
    assert engine.validate(state, Action.barrier(AgentRole.COP))


def test_barrier_quota_exhausted():
    engine = _engine()
    state = BoardState(cop=Cell(0, 0), thief=Cell(4, 4), barriers_left=0)
    assert not engine.validate(state, Action.barrier(AgentRole.COP))


def test_capture_terminal():
    engine = _engine()
    state = BoardState(cop=Cell(2, 2), thief=Cell(2, 2), barriers_left=5)
    assert engine.terminal_check(state) is SubGameOutcome.COP_WINS


def test_timeout_terminal():
    engine = _engine(max_moves=3)
    state = BoardState(cop=Cell(0, 0), thief=Cell(4, 4), barriers_left=5, move_count=6)
    assert engine.terminal_check(state) is SubGameOutcome.THIEF_WINS


def test_malformed_action_rejected():
    engine = _engine()
    state = BoardState(cop=Cell(0, 0), thief=Cell(4, 4), barriers_left=5)
    assert not engine.validate(state, "not-an-action")


def test_non_terminal_returns_none():
    engine = _engine()
    state = BoardState(cop=Cell(0, 0), thief=Cell(4, 4), barriers_left=5)
    assert engine.terminal_check(state) is None
