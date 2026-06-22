"""MovementMixin — single concern: which moves are geometrically legal.

A move is legal when the destination cell is in-bounds and not sealed by a
barrier. STAY (no displacement) is always legal.
"""

from __future__ import annotations

from ...constants import Direction
from ..board_state import BoardState
from ..grid import Cell, Grid


class MovementMixin:
    """Geometric legality of movement. Provides exactly one concern."""

    def is_move_legal(
        self, grid: Grid, state: BoardState, origin: Cell, direction: Direction
    ) -> bool:
        """True if stepping from ``origin`` in ``direction`` lands on a free cell."""
        if direction is Direction.STAY:
            return True
        target = origin.step(direction)
        return grid.in_bounds(target) and not state.is_blocked(target)

    def legal_directions(self, grid: Grid, state: BoardState, origin: Cell) -> list[Direction]:
        """All directions (incl. STAY) that are legal moves from ``origin``."""
        return [d for d in Direction if self.is_move_legal(grid, state, origin, d)]
