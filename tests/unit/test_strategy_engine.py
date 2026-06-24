"""TDD: the Angel–Devil strategy engine (features, evaluation, minimax, self-play)."""

from __future__ import annotations

import numpy as np

from cop_thief.domain.constants import ActionType, AgentRole
from cop_thief.domain.grid import Grid
from cop_thief.domain.state import DecPomdpGameState
from cop_thief.domain.strategy.evaluation import Evaluator
from cop_thief.domain.strategy.features import (
    chebyshev,
    feature_vector,
    thief_mobility,
    thief_region,
)
from cop_thief.domain.strategy.minimax import MinimaxPlanner
from cop_thief.domain.strategy.selfplay import train_weights


def _open(cop=(0, 0), thief=(2, 2)) -> DecPomdpGameState:
    return DecPomdpGameState(cop_pos=cop, thief_pos=thief, grid=Grid(shape=(5, 5)))


def test_features_normalized_and_oriented() -> None:
    """φ has 4 components in [0,1]; the Cop's cell is excluded from the Angel region."""
    state = _open()
    assert chebyshev((0, 0), (2, 3)) == 3
    assert thief_region(state) == 24  # 25 cells minus the Cop's cell
    assert thief_mobility(state) == 8
    feats = feature_vector(state)
    assert len(feats) == 4 and all(0.0 <= f <= 1.0 for f in feats)


def test_terminal_capture_trapped_and_midgame() -> None:
    """Capture and Thief-trapped score for the Cop; a mid-game leaf is finite/non-terminal."""
    ev = Evaluator()
    assert ev.terminal_value(DecPomdpGameState(cop_pos=(2, 2), thief_pos=(2, 2))) > 0
    boxed = Grid(shape=(5, 5), barriers=frozenset({(0, 1), (1, 0), (1, 1)}))
    trapped = DecPomdpGameState(cop_pos=(4, 4), thief_pos=(0, 0), grid=boxed, turn_role=AgentRole.THIEF)
    assert ev.terminal_value(trapped) > 0
    mid = _open(thief=(4, 4))
    assert ev.terminal_value(mid) is None
    assert isinstance(ev.value(mid), float)


def test_minimax_captures_adjacent_thief() -> None:
    """With the Thief one King-step away, the Cop's minimax move is the capture."""
    state = DecPomdpGameState(cop_pos=(2, 2), thief_pos=(2, 3), turn_role=AgentRole.COP)
    action_type, target = MinimaxPlanner(depth=2).best_action(state)
    assert action_type is ActionType.MOVE and target == (2, 3)


def test_minimax_offers_barrier_and_thief_avoids_suicide() -> None:
    """The Cop action set includes a self-wall; the Thief never steps onto the Cop."""
    planner = MinimaxPlanner(depth=2)
    cop_turn = DecPomdpGameState(cop_pos=(2, 2), thief_pos=(4, 4), turn_role=AgentRole.COP, cop_barriers_left=3)
    assert (ActionType.PLACE_BARRIER, (2, 2)) in planner.actions(cop_turn, AgentRole.COP)
    thief_turn = DecPomdpGameState(cop_pos=(2, 2), thief_pos=(2, 3), turn_role=AgentRole.THIEF)
    _at, target = planner.best_action(thief_turn)
    assert target != (2, 2)


def test_self_play_training_returns_finite_weights() -> None:
    """Self-play RL runs and returns four finite, clipped weights."""
    weights = train_weights(episodes=3, depth=1, seed=1)
    assert len(weights) == 4
    assert all(np.isfinite(w) and 0.0 <= w <= 5.0 for w in weights)
