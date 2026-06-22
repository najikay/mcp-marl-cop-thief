"""Unit tests for the heuristic pursuit/evasion strategy."""

from __future__ import annotations

from cop_thief.constants import AgentRole
from cop_thief.domain.board_state import BoardState
from cop_thief.domain.grid import Cell, Grid
from cop_thief.domain.rules import RulesEngine
from cop_thief.domain.strategy import HeuristicStrategy


def _chebyshev(a: Cell, b: Cell) -> int:
    return max(abs(a.row - b.row), abs(a.col - b.col))


def test_cop_closes_distance():
    rules = RulesEngine(Grid(5, 5), 25)
    state = BoardState(cop=Cell(0, 0), thief=Cell(4, 4), barriers_left=5)
    action = HeuristicStrategy().choose_action(state, AgentRole.COP, rules)
    moved = state.cop.step(action.direction)
    assert _chebyshev(moved, state.thief) < _chebyshev(state.cop, state.thief)


def test_thief_opens_distance():
    rules = RulesEngine(Grid(5, 5), 25)
    state = BoardState(cop=Cell(2, 2), thief=Cell(2, 3), barriers_left=5)
    action = HeuristicStrategy().choose_action(state, AgentRole.THIEF, rules)
    moved = state.thief.step(action.direction)
    assert _chebyshev(moved, state.cop) >= _chebyshev(state.thief, state.cop)


def test_strategy_returns_legal_action():
    rules = RulesEngine(Grid(2, 2), 25)
    state = BoardState(cop=Cell(0, 0), thief=Cell(1, 1), barriers_left=5)
    action = HeuristicStrategy().choose_action(state, AgentRole.COP, rules)
    assert rules.validate(state, action)
