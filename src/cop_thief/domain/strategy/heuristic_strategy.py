"""HeuristicStrategy — Chebyshev pursuit (Cop) and evasion (Thief).

Movement is 8-connected so Chebyshev distance ``max(|dr|, |dc|)`` is the true
step distance. The Cop minimises it; the Thief maximises it. Ties break by a
fixed :data:`MOVE_PRIORITY` order so play is deterministic and never stalls into
a passive draw. This baseline reads the opponent's true cell (full observability);
the partial-observability variant lives in :mod:`belief_strategy`.
"""

from __future__ import annotations

from ...constants import MOVE_PRIORITY, AgentRole, Direction
from ..board_state import BoardState
from ..grid import Cell
from ..rules import RulesEngine
from .base_strategy import BaseStrategy


def chebyshev(a: Cell, b: Cell) -> int:
    """Number of 8-connected steps between two cells."""
    return max(abs(a.row - b.row), abs(a.col - b.col))


def best_direction_toward(
    origin: Cell,
    target: Cell,
    pursue: bool,
    state: BoardState,
    rules: RulesEngine,
    allow_stay: bool = True,
) -> Direction:
    """Pick the legal direction that best closes (pursue) or opens distance.

    With ``allow_stay=False`` the agent must move if any non-STAY move is legal,
    so a pursuer never parks on a stale guess.
    """
    legal = [d for d in MOVE_PRIORITY if rules.is_move_legal(rules.grid, state, origin, d)]
    if not allow_stay:
        moving = [d for d in legal if d is not Direction.STAY]
        legal = moving or legal
    best_dir = legal[0] if legal else Direction.STAY
    best_dist: int | None = None
    for direction in legal:
        dist = chebyshev(origin.step(direction), target)
        if best_dist is None or (dist < best_dist if pursue else dist > best_dist):
            best_dist, best_dir = dist, direction
    return best_dir


class HeuristicStrategy(BaseStrategy):
    """Greedy distance-based pursuit/evasion against the opponent's true cell."""

    def choose_action(self, state, role, rules, belief=None):
        """Pick the legal move that best serves ``role``'s objective."""
        origin = state.cop if role is AgentRole.COP else state.thief
        target = state.thief if role is AgentRole.COP else state.cop
        pursue = role is AgentRole.COP
        return _as_move(role, best_direction_toward(origin, target, pursue, state, rules))


def _as_move(role: AgentRole, direction: Direction):
    from ..action import Action

    return Action.move(role, direction)
