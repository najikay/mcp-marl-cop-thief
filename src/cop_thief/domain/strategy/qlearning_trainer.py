"""QLearningTrainer — self-play training for the Cop's Q-table.

The Cop learns by ε-greedy self-play against an evasive opponent (the heuristic
Thief). Reward shaping comes from config: a large bonus for capture, a small step
cost (urgency), and a penalty if the Thief escapes. Returns a trained
:class:`QTable` ready for :class:`QLearningStrategy`.
"""

from __future__ import annotations

import random

from ...config.models import GameConfig
from ...config.rl_config import RLConfig
from ...constants import AgentRole
from ..board_state import BoardStateMachine
from ..grid import Grid
from ..rules import RulesEngine
from .heuristic_strategy import HeuristicStrategy
from .qtable import ACTIONS, QTable, encode_state


class QLearningTrainer:
    """Train a Cop Q-table by self-play against the heuristic Thief."""

    def __init__(self, config: GameConfig, rl: RLConfig, rng: random.Random | None = None) -> None:
        self._config = config
        self._rl = rl
        self._rng = rng or random.Random(config.seed)
        self._grid = Grid(*config.grid_size)
        self._rules = RulesEngine(self._grid, config.max_moves)
        self._machine = BoardStateMachine(self._grid, config.max_barriers)
        self._thief = HeuristicStrategy()

    def train(self, episodes: int) -> QTable:
        """Run ``episodes`` of ε-greedy self-play and return the Q-table."""
        table = QTable(self._rl.alpha, self._rl.gamma)
        epsilon = self._rl.epsilon
        for _ in range(episodes):
            self._run_episode(table, epsilon)
            epsilon = max(self._rl.epsilon_min, epsilon * self._rl.epsilon_decay)
        return table

    def _run_episode(self, table: QTable, epsilon: float) -> None:
        state = self._machine.initial_state(self._config.random_start, self._rng)
        for _ in range(self._config.max_moves):
            key = encode_state(state, self._grid)
            action_idx = self._select(state, key, table, epsilon)
            state = self._machine.apply(state, self._cop_move(action_idx))
            if self._rules.is_capture(state):
                table.update(key, action_idx, self._rl.reward_capture, 0, True)
                return
            state = self._machine.apply(state, self._thief_move(state))
            done = self._rules.is_capture(state)
            reward = self._rl.reward_step + (self._rl.reward_capture if done else 0.0)
            table.update(key, action_idx, reward, encode_state(state, self._grid), done)
            if done:
                return
        # Thief survived the episode: penalise the final decision.
        table.update(encode_state(state, self._grid), 0, self._rl.reward_escape, 0, True)

    def _select(self, state, key, table: QTable, epsilon: float) -> int:
        legal = [
            i
            for i, d in enumerate(ACTIONS)
            if self._rules.is_move_legal(self._grid, state, state.cop, d)
        ]
        if self._rng.random() < epsilon:
            return self._rng.choice(legal)
        return table.greedy_index(key, legal)

    def _cop_move(self, action_idx: int):
        from ..action import Action

        return Action.move(AgentRole.COP, ACTIONS[action_idx])

    def _thief_move(self, state):
        return self._thief.choose_action(state, AgentRole.THIEF, self._rules)
