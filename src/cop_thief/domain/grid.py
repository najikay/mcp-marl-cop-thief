"""Immutable 2-D board model with pure spatial-legality helpers.

``Grid`` is a frozen Pydantic model so it is hashable, network-serializable, and
safe to share across MCP/gatekeeper boundaries without defensive copying.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

Coord = tuple[int, int]


class Grid(BaseModel):
    """Board shape plus the set of impassable barrier cells (immutable)."""

    model_config = ConfigDict(frozen=True)

    shape: tuple[int, int] = (5, 5)
    barriers: frozenset[Coord] = Field(default_factory=frozenset)

    def is_within_bounds(self, pos: Coord) -> bool:
        """Return True if ``pos`` lies inside the board.

        Input: a ``(row, col)`` coordinate. Output: bool.
        """
        row, col = pos
        return 0 <= row < self.shape[0] and 0 <= col < self.shape[1]

    def is_barrier(self, pos: Coord) -> bool:
        """Return True if ``pos`` holds an active barrier (wall)."""
        return pos in self.barriers

    def is_legal_move(self, from_pos: Coord, to_pos: Coord) -> bool:
        """Return True if a single step from ``from_pos`` to ``to_pos`` is legal.

        Legal means the target is in-bounds, not a barrier, and at most one cell
        away in any direction (Chebyshev distance ≤ 1, diagonals allowed; STAY
        permitted). Edge case: a move onto a barrier or off-board is rejected.
        """
        if not self.is_within_bounds(to_pos) or self.is_barrier(to_pos):
            return False
        d_row = abs(from_pos[0] - to_pos[0])
        d_col = abs(from_pos[1] - to_pos[1])
        return max(d_row, d_col) <= 1
