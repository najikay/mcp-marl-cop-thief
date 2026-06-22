"""Tkinter app: animate a Cop & Thief game frame by frame.

Loads frames from the SDK (single entrypoint), then plays/pauses/steps through
them on a canvas, showing each agent's natural-language message. Excluded from
coverage (requires a display). Launch with ``uv run cop-thief-gui``.
"""

from __future__ import annotations

import tkinter as tk

from ..sdk import CopThiefSDK
from .board_view import BoardView

_DELAY_MS = 600


class GameWindow:  # pragma: no cover - interactive UI
    """A window that animates one recorded sub-game at a time."""

    def __init__(self, sdk: CopThiefSDK | None = None) -> None:
        # Full-observability heuristic: visually engaging (real captures) while
        # still showing each agent's free-NL message. Partial-observability play
        # exists too, but its coarse region-belief tends to stalemate.
        self._sdk = sdk or CopThiefSDK()
        rows, cols = self._sdk.config.grid_size
        self._root = tk.Tk()
        self._root.title("Cop & Thief — Dec-POMDP pursuit")
        self._canvas = tk.Canvas(self._root, highlightthickness=0, bg="white")
        self._view = BoardView(self._canvas, rows, cols)
        w, h = self._view.pixel_size
        self._canvas.configure(width=w, height=h)
        self._canvas.pack(padx=8, pady=8)
        self._status = tk.Label(self._root, text="", wraplength=w, font=("Segoe UI", 11))
        self._status.pack(padx=8, pady=(0, 8))
        self._controls()
        self._frames: list[dict] = []
        self._index = 0
        self._playing = False
        self.new_game()

    def _controls(self) -> None:
        bar = tk.Frame(self._root)
        bar.pack(pady=(0, 8))
        for label, command in (
            ("▶ Play", self.play),
            ("⏸ Pause", self.pause),
            ("⏭ Step", self.step),
            ("🔄 New game", self.new_game),
        ):
            tk.Button(bar, text=label, command=command, width=10).pack(side=tk.LEFT, padx=4)

    def new_game(self) -> None:
        """Record a fresh sub-game and show its first frame."""
        self._frames = self._sdk.record_sub_game()
        self._index = 0
        self._playing = False
        self._show()

    def play(self) -> None:
        if not self._playing:
            self._playing = True
            self._tick()

    def pause(self) -> None:
        self._playing = False

    def step(self) -> None:
        self._playing = False
        self._advance()

    def _tick(self) -> None:
        if not self._playing:
            return
        if not self._advance():
            self._playing = False
            return
        self._root.after(_DELAY_MS, self._tick)

    def _advance(self) -> bool:
        if self._index >= len(self._frames) - 1:
            return False
        self._index += 1
        self._show()
        return True

    def _show(self) -> None:
        frame = self._frames[self._index]
        self._view.render(frame)
        message = frame.get("message") or "Start position"
        self._status.configure(text=f"[{self._index}/{len(self._frames) - 1}]  {message}")

    def run(self) -> None:
        self._root.mainloop()


def main() -> None:  # pragma: no cover - interactive UI
    """Console entrypoint: open the visualization window."""
    GameWindow().run()


if __name__ == "__main__":
    main()
