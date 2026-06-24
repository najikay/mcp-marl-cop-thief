"""Cop-oriented game-theoretic features for the Angel–Devil evaluation.

Each feature is normalized to roughly [0, 1] and oriented so that a *higher* value
is better for the Cop (the Devil). ``thief_region`` is the size of the Thief's
(Angel's) free reachable region by flood fill — the quantity the Devil shrinks.
"""

from __future__ import annotations

from collections import deque

from cop_thief.domain.constants import AgentRole
from cop_thief.domain.geometry import get_adjacent_coords
from cop_thief.domain.state import DecPomdpGameState

Coord = tuple[int, int]


def chebyshev(a: Coord, b: Coord) -> int:
    """Return the Chebyshev (King-move) distance between two cells."""
    return max(abs(a[0] - b[0]), abs(a[1] - b[1]))


def thief_region(state: DecPomdpGameState) -> int:
    """Flood-fill the cells the Thief can still reach (King steps, barriers/Cop block)."""
    start = state.thief_pos
    seen = {start}
    queue = deque([start])
    while queue:
        cur = queue.popleft()
        for nb in get_adjacent_coords(cur, state.grid.shape):
            if nb not in seen and not state.grid.is_barrier(nb) and nb != state.cop_pos:
                seen.add(nb)
                queue.append(nb)
    return len(seen)


def thief_mobility(state: DecPomdpGameState) -> int:
    """Return the count of the Thief's immediate legal (non-STAY) moves."""
    return len(state.legal_moves(AgentRole.THIEF))


def feature_vector(state: DecPomdpGameState) -> tuple[float, ...]:
    """Return the normalized cop-positive feature tuple φ(s)."""
    rows, cols = state.grid.shape
    diag = max(rows, cols)
    area = rows * cols
    return (
        1.0 - chebyshev(state.cop_pos, state.thief_pos) / diag,  # proximity
        1.0 - thief_region(state) / area,                        # containment
        1.0 - thief_mobility(state) / 8.0,                       # immobilization
        state.cop_barriers_left / 5.0,                           # resources
    )
