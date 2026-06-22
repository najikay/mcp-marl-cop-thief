"""Grid and Cell — the spatial substrate of the Dec-POMDP state space ``S``.

A :class:`Cell` is an immutable ``(row, col)`` coordinate; a :class:`Grid`
knows its bounds (sourced from config, never literals) and computes neighbours.
"""

from __future__ import annotations

from dataclasses import dataclass

from ..constants import Direction


@dataclass(frozen=True)
class Cell:
    """An immutable board coordinate. Frozen so it is hashable for barrier sets."""

    row: int
    col: int

    def step(self, direction: Direction) -> Cell:
        """Return the neighbouring cell one step in ``direction`` (unclamped)."""
        dr, dc = direction.vector
        return Cell(self.row + dr, self.col + dc)


class Grid:
    """A ``rows × cols`` board. Dimensions come from config, not magic numbers."""

    def __init__(self, rows: int, cols: int) -> None:
        if rows < 1 or cols < 1:
            raise ValueError(f"grid dimensions must be positive, got ({rows}, {cols})")
        self.rows = rows
        self.cols = cols

    def in_bounds(self, cell: Cell) -> bool:
        """True if ``cell`` lies within the board rectangle."""
        return 0 <= cell.row < self.rows and 0 <= cell.col < self.cols

    def neighbors(self, cell: Cell, include_diagonal: bool = True) -> list[Cell]:
        """Return all in-bounds neighbours of ``cell`` (8-connected by default)."""
        result = []
        for direction in Direction:
            if direction is Direction.STAY:
                continue
            dr, dc = direction.vector
            if not include_diagonal and dr != 0 and dc != 0:
                continue
            candidate = cell.step(direction)
            if self.in_bounds(candidate):
                result.append(candidate)
        return result

    def cells(self) -> list[Cell]:
        """Enumerate every cell on the board (row-major order)."""
        return [Cell(r, c) for r in range(self.rows) for c in range(self.cols)]
