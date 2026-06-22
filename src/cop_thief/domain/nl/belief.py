"""BeliefUpdate — what a receiver infers from an opponent's free-text message.

The protocol never carries coordinates (PRD KPI K1); instead each message leaks
qualitative spatial cues. A :class:`BeliefUpdate` captures the recovered region
band, an optional movement direction, whether a barrier was mentioned, and a
confidence in the parse. It can project the region back to a representative cell
so a strategy can act on it.
"""

from __future__ import annotations

from dataclasses import dataclass

from ...constants import Direction
from ..grid import Cell, Grid

ROW_BANDS = ("north", "central", "south")
COL_BANDS = ("west", "central", "east")

# Substring cues a parser scans for ("northern" contains "north", etc.).
ROW_SYNONYMS = {
    "north": ("north", "upper", "top"),
    "central": ("central", "middle", "midfield", "centre", "center"),
    "south": ("south", "lower", "bottom"),
}
COL_SYNONYMS = {
    "west": ("west", "left"),
    "central": ("central", "middle", "centre", "center"),
    "east": ("east", "right"),
}
DIRECTION_PHRASES = {
    Direction.N: "north",
    Direction.NE: "north-east",
    Direction.E: "east",
    Direction.SE: "south-east",
    Direction.S: "south",
    Direction.SW: "south-west",
    Direction.W: "west",
    Direction.NW: "north-west",
    Direction.STAY: "holding position",
}


def _band_center(band: str | None, size: int) -> int:
    """Map a band label to a representative index along an axis of length ``size``."""
    if band in ("north", "west"):
        return size // 6
    if band in ("south", "east"):
        return min(size - 1, (5 * size) // 6)
    return size // 2  # central or unknown


@dataclass(frozen=True)
class BeliefUpdate:
    """A parsed, actionable belief about the opponent's whereabouts."""

    region_row: str | None
    region_col: str | None
    moved: Direction | None
    barrier_mentioned: bool
    confidence: float

    @classmethod
    def unknown(cls) -> BeliefUpdate:
        """A safe, zero-confidence default when nothing could be parsed."""
        return cls(None, None, None, False, 0.0)

    def estimate_cell(self, grid: Grid) -> Cell | None:
        """Project the recovered region onto a representative cell, if any."""
        if self.region_row is None and self.region_col is None:
            return None
        row = _band_center(self.region_row, grid.rows)
        col = _band_center(self.region_col, grid.cols)
        return Cell(row, col)
