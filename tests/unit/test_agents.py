"""Unit tests for agent turn-taking and narration."""

from __future__ import annotations

from cop_thief.constants import AgentRole
from cop_thief.domain.action import Action
from cop_thief.domain.agents import CopAgent, ThiefAgent
from cop_thief.domain.board_state import BoardState
from cop_thief.domain.grid import Cell, Grid
from cop_thief.domain.rules import RulesEngine
from cop_thief.domain.strategy import HeuristicStrategy


def test_cop_takes_legal_turn_with_message():
    rules = RulesEngine(Grid(5, 5), 25)
    state = BoardState(cop=Cell(0, 0), thief=Cell(4, 4), barriers_left=5)
    turn = CopAgent(HeuristicStrategy()).take_turn(state, rules)
    assert rules.validate(state, turn.action)
    assert turn.message.startswith("Cop:")


def test_thief_role_and_narration():
    thief = ThiefAgent(HeuristicStrategy())
    assert thief.role is AgentRole.THIEF
    msg = thief.narrate(Action.move(AgentRole.THIEF, list(rules_dirs())[0]))
    assert msg.startswith("Thief:")


def test_cop_barrier_narration():
    cop = CopAgent(HeuristicStrategy())
    assert "barrier" in cop.narrate(Action.barrier(AgentRole.COP))


def rules_dirs():
    from cop_thief.constants import Direction

    return Direction
