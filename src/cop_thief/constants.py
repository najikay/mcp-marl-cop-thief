"""Immutable enums and physical constants for the Dec-POMDP pursuit.

These exist so that no direction vector, role, action kind or outcome label is
ever hardcoded as a magic literal elsewhere in the code base.
"""

from __future__ import annotations

from enum import Enum


class Direction(Enum):
    """The 8 grid directions plus STAY, each carrying a ``(dr, dc)`` step vector."""

    N = (-1, 0)
    NE = (-1, 1)
    E = (0, 1)
    SE = (1, 1)
    S = (1, 0)
    SW = (1, -1)
    W = (0, -1)
    NW = (-1, -1)
    STAY = (0, 0)

    @property
    def vector(self) -> tuple[int, int]:
        """Return the ``(delta_row, delta_col)`` movement vector for this direction."""
        return self.value


# Deterministic tie-break order used by strategies to avoid draws.
MOVE_PRIORITY: tuple[Direction, ...] = (
    Direction.NE,
    Direction.SE,
    Direction.SW,
    Direction.NW,
    Direction.N,
    Direction.E,
    Direction.S,
    Direction.W,
    Direction.STAY,
)


class AgentRole(Enum):
    """The two players. Only the COP may place barriers."""

    COP = "cop"
    THIEF = "thief"


class ActionType(Enum):
    """What an agent does on its turn: move in a direction or seal its cell."""

    MOVE = "move"
    PLACE_BARRIER = "place_barrier"


class SubGameOutcome(Enum):
    """Terminal result of a single sub-game."""

    COP_WINS = "cop_wins"
    THIEF_WINS = "thief_wins"
    VOID_TECHNICAL = "void_technical"
