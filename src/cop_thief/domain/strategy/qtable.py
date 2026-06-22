"""QTable — the tabular Q-function with the Bellman update (PLAN Phase 7.E).

State is the joint ``(cop, thief)`` position encoded to one integer; actions are
the nine :class:`Direction` members. The update implements
``Q(s,a) ← Q(s,a) + α[r + γ·maxₐ′Q(s′,a′) − Q(s,a)]``. Rows are created lazily so
the table stays sparse, and it serialises to JSON for reuse.
"""

from __future__ import annotations

import json
from pathlib import Path

from ...constants import Direction
from ..board_state import BoardState
from ..grid import Grid

ACTIONS: tuple[Direction, ...] = tuple(Direction)


def encode_state(state: BoardState, grid: Grid) -> int:
    """Encode the joint cop/thief positions into a single integer key."""
    cells = grid.rows * grid.cols
    cop = state.cop.row * grid.cols + state.cop.col
    thief = state.thief.row * grid.cols + state.thief.col
    return cop * cells + thief


class QTable:
    """A sparse Q-table with ε-greedy selection and the Bellman update."""

    def __init__(self, alpha: float, gamma: float) -> None:
        self._alpha = alpha
        self._gamma = gamma
        self._q: dict[int, list[float]] = {}

    def _row(self, key: int) -> list[float]:
        return self._q.setdefault(key, [0.0] * len(ACTIONS))

    def best_value(self, key: int) -> float:
        """Maximum Q-value attainable from ``key`` (0 for an unseen state)."""
        return max(self._row(key))

    def greedy_index(self, key: int, allowed: list[int]) -> int:
        """Index of the highest-valued allowed action (first wins ties)."""
        row = self._row(key)
        return max(allowed, key=lambda i: row[i])

    def update(self, key: int, action: int, reward: float, next_key: int, done: bool) -> None:
        """Apply one Bellman temporal-difference update in place."""
        future = 0.0 if done else self._gamma * self.best_value(next_key)
        row = self._row(key)
        row[action] += self._alpha * (reward + future - row[action])

    def save(self, path: str | Path) -> None:
        """Persist the table to JSON (results dir)."""
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps({str(k): v for k, v in self._q.items()}), encoding="utf-8")

    @classmethod
    def load(cls, path: str | Path, alpha: float, gamma: float) -> QTable:
        """Load a table previously written by :meth:`save`."""
        table = cls(alpha, gamma)
        raw = json.loads(Path(path).read_text(encoding="utf-8"))
        table._q = {int(k): list(v) for k, v in raw.items()}
        return table
