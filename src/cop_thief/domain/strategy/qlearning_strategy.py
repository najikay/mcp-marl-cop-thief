"""QLearningStrategy — greedy play from a trained Q-table (the pursuer).

Drop-in alternative to :class:`HeuristicStrategy` for the Cop: it reads the joint
true positions (full observability, like the heuristic baseline) and plays the
highest-valued legal move from a pre-trained :class:`QTable`. Training lives in
:mod:`qlearning_trainer`.
"""

from __future__ import annotations

from ...constants import AgentRole
from ..action import Action
from .base_strategy import BaseStrategy
from .qtable import ACTIONS, QTable, encode_state


class QLearningStrategy(BaseStrategy):
    """Exploit a trained Q-table to choose the pursuer's move."""

    def __init__(self, qtable: QTable) -> None:
        self._q = qtable

    def choose_action(self, state, role, rules, belief=None):
        """Greedy legal action from the Q-table for ``role`` (intended: Cop)."""
        origin = state.cop if role is AgentRole.COP else state.thief
        legal = [
            i
            for i, direction in enumerate(ACTIONS)
            if rules.is_move_legal(rules.grid, state, origin, direction)
        ]
        key = encode_state(state, rules.grid)
        best = self._q.greedy_index(key, legal)
        return Action.move(role, ACTIONS[best])
