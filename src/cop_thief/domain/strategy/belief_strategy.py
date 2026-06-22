"""BeliefHeuristicStrategy — faithful partial-observability pursuit/evasion.

Unlike the baseline, this strategy never reads the opponent's true cell. It acts
only on the :class:`BeliefUpdate` parsed from the opponent's natural-language
message, projected to a representative target cell. With no belief yet it falls
back to exploring toward the board centre (a safe default, PLAN §4.3).
"""

from __future__ import annotations

from ...constants import AgentRole
from ..grid import Cell
from .base_strategy import BaseStrategy
from .heuristic_strategy import best_direction_toward


class BeliefHeuristicStrategy(BaseStrategy):
    """Decide using only the inferred belief about the opponent's region."""

    def choose_action(self, state, role, rules, belief=None):
        """Pursue/evade the believed opponent cell, not the true one."""
        origin = state.cop if role is AgentRole.COP else state.thief
        target = self._target(belief, rules, origin)
        pursue = role is AgentRole.COP
        direction = best_direction_toward(origin, target, pursue, state, rules)
        from ..action import Action

        return Action.move(role, direction)

    @staticmethod
    def _target(belief, rules, origin: Cell) -> Cell:
        """Believed opponent cell, or the board centre when nothing is known."""
        if belief is not None:
            estimated = belief.estimate_cell(rules.grid)
            if estimated is not None:
                return estimated
        return Cell(rules.grid.rows // 2, rules.grid.cols // 2)
