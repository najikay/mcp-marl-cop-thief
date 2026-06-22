"""BoardView — draw a single game frame on a Tkinter canvas.

Pure rendering: given a frame ``{cop, thief, barriers}`` it paints the grid,
sealed cells, and the two agents. Kept separate from the app so the drawing is
easy to reason about. Excluded from coverage (requires a display).
"""

from __future__ import annotations

_CELL = 84
_PAD = 10
_COP = "#2563eb"
_THIEF = "#dc2626"
_BARRIER = "#1f2937"
_GRID = "#cbd5e1"


class BoardView:
    """Render frames for an ``rows x cols`` board onto a canvas."""

    def __init__(self, canvas, rows: int, cols: int) -> None:
        self._canvas = canvas
        self._rows = rows
        self._cols = cols

    def render(self, frame: dict) -> None:
        """Clear and redraw the board for one frame."""
        self._canvas.delete("all")
        self._draw_grid()
        for cell in frame.get("barriers", []):
            self._fill(cell[0], cell[1], _BARRIER)
        self._token(frame["thief"][0], frame["thief"][1], _THIEF)
        self._token(frame["cop"][0], frame["cop"][1], _COP)

    def _draw_grid(self) -> None:
        for r in range(self._rows):
            for c in range(self._cols):
                x, y = self._origin(r, c)
                self._canvas.create_rectangle(x, y, x + _CELL, y + _CELL, outline=_GRID, width=2)

    def _fill(self, r: int, c: int, color: str) -> None:
        x, y = self._origin(r, c)
        self._canvas.create_rectangle(x, y, x + _CELL, y + _CELL, fill=color, outline=color)

    def _token(self, r: int, c: int, color: str) -> None:
        x, y = self._origin(r, c)
        m = 16
        self._canvas.create_oval(x + m, y + m, x + _CELL - m, y + _CELL - m, fill=color, outline="")

    @staticmethod
    def _origin(r: int, c: int) -> tuple[int, int]:
        return _PAD + c * _CELL, _PAD + r * _CELL

    @property
    def pixel_size(self) -> tuple[int, int]:
        """Canvas width/height needed for the whole board."""
        return _PAD * 2 + self._cols * _CELL, _PAD * 2 + self._rows * _CELL
