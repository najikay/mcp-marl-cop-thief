"""Self-play reinforcement learning: tune the Angel–Devil evaluation weights.

Advanced multi-agent RL beyond the assignment's tabular Q: both sides act by
minimax over the *current* linear value (with ε-exploration for coverage), and the
weights are regressed toward minimax-backed game outcomes across self-play episodes
(Angel-vs-Devil co-evolution). ``train_weights`` returns the learned weight tuple.
"""

from __future__ import annotations

import random

import numpy as np

from cop_thief.domain.geometry import random_start_positions
from cop_thief.domain.grid import Grid
from cop_thief.domain.state import DecPomdpGameState
from cop_thief.domain.strategy.evaluation import Evaluator
from cop_thief.domain.strategy.features import feature_vector
from cop_thief.domain.strategy.minimax import MinimaxPlanner


def _rollout(weights, depth, max_moves, rng, epsilon):
    """Play one ε-greedy self-play game from a random opening; return (states, outcome)."""
    ev = Evaluator(weights, max_moves)
    planner = MinimaxPlanner(ev, depth)
    cop0, thief0 = random_start_positions(5, 5, rng)
    state = DecPomdpGameState(cop_pos=cop0, thief_pos=thief0, grid=Grid(shape=(5, 5)))
    visited = []
    for _ in range(max_moves * 2):
        outcome = ev.terminal_value(state)
        if outcome is not None:
            return visited, float(np.sign(outcome))
        visited.append(state)
        acts = planner.actions(state, state.turn_role)
        action = acts[rng.randrange(len(acts))] if rng.random() < epsilon else planner.best_action(state)
        state = state.apply_action(state.turn_role, *action)
    return visited, float(np.sign(ev.terminal_value(state) or -1.0))


def train_weights(episodes=20, depth=2, lr=0.03, epsilon=0.2, max_moves=25, seed=0):
    """Run self-play episodes and return weights whose value predicts cop-signed outcomes."""
    rng = random.Random(seed)
    weights = np.array(Evaluator().weights, dtype=float)
    for _ in range(episodes):
        visited, outcome = _rollout(tuple(weights), depth, max_moves, rng, epsilon)
        for state in visited:
            feats = np.array(feature_vector(state))
            weights += lr * (outcome - np.tanh(float(feats @ weights))) * feats
        weights = np.clip(weights, 0.0, 5.0)
    return tuple(float(w) for w in weights)
