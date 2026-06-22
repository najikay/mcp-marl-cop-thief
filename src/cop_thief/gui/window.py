"""UI-01 native tkinter Observer Canvas (zero extra dependencies).

Two-pane live observer: a 5x5 grid canvas (Blue oval = Cop, Red rectangle =
Thief, dark-gray blocks = Barriers) and a scrolling NL-banter feed. Updates are
delivered through a thread-safe ``queue.Queue`` and consumed via ``after`` polling
so the GUI never blocks the MARL loop.
"""

from __future__ import annotations

import queue
import tkinter as tk

_TILE = 80
_CANVAS = 400
_POLL_MS = 100


class ObserverGUI:
    """A non-blocking tkinter observer for the Dec-POMDP pursuit."""

    def __init__(self, grid_size: int = 5) -> None:
        """Build the two-pane window and start the queue poller."""
        self.grid_size = grid_size
        self.render_queue: queue.Queue = queue.Queue()
        self.root = tk.Tk()
        self.root.title("Dec-POMDP Pursuit Observer")
        self.root.geometry("800x500")
        self.canvas = tk.Canvas(self.root, width=_CANVAS, height=_CANVAS, bg="white")
        self.canvas.pack(side=tk.LEFT, padx=10, pady=10)
        self.feed = tk.Text(self.root, width=44, wrap="word")
        self.feed.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        self._draw_grid()
        self.root.after(_POLL_MS, self._poll_queue)

    def _draw_grid(self) -> None:
        """Render the static grid lines."""
        span = self.grid_size * _TILE
        for i in range(self.grid_size + 1):
            self.canvas.create_line(0, i * _TILE, span, i * _TILE)
            self.canvas.create_line(i * _TILE, 0, i * _TILE, span)

    def _cell_bbox(self, row: int, col: int, pad: int = 10) -> tuple:
        """Return the padded pixel bounding box of grid cell (row, col)."""
        x0, y0 = col * _TILE + pad, row * _TILE + pad
        return x0, y0, x0 + _TILE - 2 * pad, y0 + _TILE - 2 * pad

    def _render(self, snapshot, prose, sender_role) -> None:
        """Redraw agents/barriers and append prose to the feed."""
        self.canvas.delete("agents")
        for barrier in snapshot.grid.barriers:
            box = self._cell_bbox(barrier[0], barrier[1], pad=4)
            self.canvas.create_rectangle(*box, fill="dark gray", tags="agents")
        self.canvas.create_oval(
            *self._cell_bbox(*snapshot.cop_pos), fill="blue", tags="agents"
        )
        self.canvas.create_rectangle(
            *self._cell_bbox(*snapshot.thief_pos), fill="red", tags="agents"
        )
        if prose:
            label = getattr(sender_role, "value", sender_role)
            self.feed.insert(tk.END, f'[{label}]: "{prose}"\n')
            self.feed.see(tk.END)

    def _poll_queue(self) -> None:
        """Drain all pending render items, then reschedule the poller."""
        try:
            while True:
                self._render(*self.render_queue.get_nowait())
        except queue.Empty:
            pass
        self.root.after(_POLL_MS, self._poll_queue)

    def dispatch_update(self, state_snapshot, prose_message, sender_role) -> None:
        """Thread-safe entrypoint: enqueue a render update from any thread."""
        self.render_queue.put((state_snapshot, prose_message, sender_role))
