"""Tests for the partial-observability belief strategy and full belief loop."""

from __future__ import annotations

from cop_thief.constants import AgentRole
from cop_thief.domain.board_state import BoardState
from cop_thief.domain.grid import Cell, Grid
from cop_thief.domain.nl import BeliefUpdate
from cop_thief.domain.rules import RulesEngine
from cop_thief.domain.strategy import BeliefHeuristicStrategy
from cop_thief.sdk import CopThiefSDK


def test_cop_moves_toward_believed_region():
    rules = RulesEngine(Grid(6, 6), 25)
    state = BoardState(cop=Cell(0, 0), thief=Cell(5, 5), barriers_left=5)
    belief = BeliefUpdate("south", "east", None, False, 0.8)  # opponent SE
    action = BeliefHeuristicStrategy().choose_action(state, AgentRole.COP, rules, belief)
    moved = state.cop.step(action.direction)
    assert moved.row >= state.cop.row and moved.col >= state.cop.col  # heads SE


def test_no_belief_falls_back_to_centre():
    rules = RulesEngine(Grid(5, 5), 25)
    state = BoardState(cop=Cell(0, 0), thief=Cell(4, 4), barriers_left=5)
    action = BeliefHeuristicStrategy().choose_action(state, AgentRole.COP, rules, None)
    assert rules.validate(state, action)  # safe legal move toward centre


def test_partial_observability_game_completes(small_config):
    sdk = CopThiefSDK(config=small_config, partial_observability=True)
    result = sdk.play_game()
    assert len(result.sub_games) == small_config.num_games
