"""Tabular Q-Learning strategy (per PRD_rl_qtable.md).

Implements the Bellman TD-target update and epsilon-greedy decay over a bucketed
state index (positions + active-barrier count). When a state's Q-row is
uninformed, selection defers to an injected geometric fallback (Tier-2).
"""

from __future__ import annotations

import random

import numpy as np

from cop_thief.config import get_config_manager
from cop_thief.domain.constants import AgentRole, Direction
from cop_thief.domain.state import DecPomdpGameState

_ACTIONS = list(Direction)


class QTableStrategy:
    """Off-policy tabular Q-learner with a bucketed, immutable state index."""

    def __init__(self, grid_shape: tuple[int, int] | None = None) -> None:
        """Size the Q-table from the grid and load RL hyper-parameters."""
        setup = get_config_manager().get_setup()
        self.rl = setup.rl
        rows, cols = grid_shape or tuple(setup.game.grid_size)
        self._cols = cols
        self._n = rows * cols
        self._buckets = setup.game.max_barriers + 1
        self.q = np.zeros((self._n * self._n * self._buckets, len(_ACTIONS)))
        self.epsilon = self.rl.epsilon_start
        self._last: tuple[int, int] | None = None

    def _state_index(self, state: DecPomdpGameState) -> int:
        """Flatten (cop, thief, barrier-bucket) into a single table row."""
        cop = state.cop_pos[0] * self._cols + state.cop_pos[1]
        thief = state.thief_pos[0] * self._cols + state.thief_pos[1]
        bucket = min(len(state.grid.barriers), self._buckets - 1)
        return (cop * self._n + thief) * self._buckets + bucket

    @staticmethod
    def _pos(state: DecPomdpGameState, role: AgentRole) -> tuple[int, int]:
        return state.cop_pos if role is AgentRole.COP else state.thief_pos

    def _legal(self, state: DecPomdpGameState, role: AgentRole) -> list[tuple[int, tuple]]:
        """Return legal (action_index, target) pairs, excluding STAY for K5.

        STAY is only offered when the agent has no other legal move (boxed in),
        so the learned policy never voluntarily wastes a turn (draw avoidance).
        """
        pos = self._pos(state, role)
        pairs = []
        for idx, direction in enumerate(_ACTIONS):
            if direction is Direction.STAY:
                continue
            target = (pos[0] + direction.value[0], pos[1] + direction.value[1])
            if state.grid.is_legal_move(pos, target):
                pairs.append((idx, target))
        if not pairs:
            pairs.append((_ACTIONS.index(Direction.STAY), pos))
        return pairs

    def is_informed(self, state: DecPomdpGameState, role: AgentRole) -> bool:
        """True when the top two legal Q-values differ by the confidence margin."""
        legal = self._legal(state, role)
        if len(legal) < 2:
            return False
        row = self.q[self._state_index(state)]
        values = sorted((row[idx] for idx, _ in legal), reverse=True)
        return (values[0] - values[1]) >= self.rl.q_confidence_margin

    @staticmethod
    def _match(legal: list[tuple[int, tuple]], target: tuple) -> tuple[int, tuple]:
        for idx, cell in legal:
            if cell == target:
                return idx, cell
        return legal[0]

    def select_target(self, state: DecPomdpGameState, role: AgentRole, fallback=None) -> tuple:
        """Epsilon-greedy target: Q-argmax if informed, else fallback/explore."""
        legal = self._legal(state, role)
        if not legal:
            self._last = None
            return self._pos(state, role)
        s_idx = self._state_index(state)
        explore = random.random() < self.epsilon
        if not explore and self.is_informed(state, role):
            idx, target = max(legal, key=lambda pair: self.q[s_idx, pair[0]])
        elif not explore and fallback is not None:
            idx, target = self._match(legal, fallback(state, role))
        else:
            idx, target = random.choice(legal)
        self._last = (s_idx, idx)
        return target

    def observe(self, reward: float, next_state: DecPomdpGameState, done: bool) -> None:
        """Apply the Bellman TD update for the last selected (state, action)."""
        if self._last is None:
            return
        s_idx, a_idx = self._last
        best_next = 0.0 if done else float(np.max(self.q[self._state_index(next_state)]))
        td_target = reward + self.rl.gamma * best_next
        self.q[s_idx, a_idx] += self.rl.alpha * (td_target - self.q[s_idx, a_idx])
        self._last = None

    def decay_epsilon(self) -> None:
        """Anneal exploration toward the configured floor."""
        self.epsilon = max(self.rl.epsilon_min, self.epsilon * self.rl.epsilon_decay)
