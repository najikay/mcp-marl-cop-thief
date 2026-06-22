"""HeuristicStrategy — Chebyshev pursuit (Cop) and evasion (Thief).

Movement is 8-connected so Chebyshev distance ``max(|dr|, |dc|)`` is the true
step distance. The Cop minimises it; the Thief maximises it. Ties break by a
fixed :data:`MOVE_PRIORITY` order so play is deterministic and never stalls into
a passive draw.
"""

from __future__ import annotations

from ...constants import MOVE_PRIORITY, AgentRole, Direction
from ..action import Action
from ..board_state import BoardState
from ..grid import Cell
from ..rules import RulesEngine
from .base_strategy import BaseStrategy


def _chebyshev(a: Cell, b: Cell) -> int:
    """Number of 8-connected steps between two cells."""
    return max(abs(a.row - b.row), abs(a.col - b.col))


class HeuristicStrategy(BaseStrategy):
    """Greedy distance-based pursuit/evasion with deterministic tie-breaks."""

    def choose_action(self, state: BoardState, role: AgentRole, rules: RulesEngine) -> Action:
        """Pick the legal move that best serves ``role``'s objective."""
        origin = state.cop if role is AgentRole.COP else state.thief
        opponent = state.thief if role is AgentRole.COP else state.cop
        legal = [d for d in MOVE_PRIORITY if rules.is_move_legal(rules.grid, state, origin, d)]
        best = self._best_direction(origin, opponent, role, legal)
        return Action.move(role, best)

    @staticmethod
    def _best_direction(
        origin: Cell, opponent: Cell, role: AgentRole, legal: list[Direction]
    ) -> Direction:
        """Choose the distance-optimal direction; ``legal`` is priority-ordered."""
        pursue = role is AgentRole.COP
        best_dir = Direction.STAY
        best_dist: int | None = None
        for direction in legal:
            dist = _chebyshev(origin.step(direction), opponent)
            if best_dist is None or (dist < best_dist if pursue else dist > best_dist):
                best_dist, best_dir = dist, direction
        return best_dir
