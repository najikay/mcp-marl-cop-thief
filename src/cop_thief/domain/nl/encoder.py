"""NLEncoder — turn a private board position into free natural-language prose.

The message reveals only *qualitative* spatial cues (region band + movement),
never numeric coordinates, satisfying the natural-language-only protocol. Later
versions can add deception (a Thief that bluffs about its region).
"""

from __future__ import annotations

from ...constants import AgentRole, Direction
from ..grid import Cell
from .belief import DIRECTION_PHRASES


def _row_band(row: int, rows: int) -> str:
    """Classify a row into north / central / south thirds."""
    if row * 3 < rows:
        return "north"
    if row * 3 >= 2 * rows:
        return "south"
    return "central"


def _col_band(col: int, cols: int) -> str:
    """Classify a column into west / central / east thirds."""
    if col * 3 < cols:
        return "west"
    if col * 3 >= 2 * cols:
        return "east"
    return "central"


def _region_phrase(row_band: str, col_band: str) -> str:
    """Compose a human region phrase from the two band labels."""
    if row_band == "central" and col_band == "central":
        return "centre"
    parts = [b for b in (row_band, col_band) if b != "central"]
    return "-".join(parts) + " area"


class NLEncoder:
    """Render an agent's own position and intent as opponent-facing prose."""

    def describe(
        self, cell: Cell, rows: int, cols: int, role: AgentRole, direction: Direction
    ) -> str:
        """Produce a free-text message describing region and movement (no coords)."""
        region = _region_phrase(_row_band(cell.row, rows), _col_band(cell.col, cols))
        move = DIRECTION_PHRASES[direction]
        label = role.value.capitalize()
        if role is AgentRole.COP:
            return f"{label}: closing in from the {region}, pressing {move}."
        return f"{label}: slipping through the {region}, breaking {move}."
