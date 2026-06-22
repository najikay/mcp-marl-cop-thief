"""Immutable domain enumerations for the Dec-POMDP Cop & Thief game.

Enums are the canonical, network-serializable vocabulary shared by every layer
(SDK, MCP servers, gatekeeper). They are defined once here to guarantee a single
source of truth (DRY) and to keep movement vectors consistent everywhere.
"""

from __future__ import annotations

from enum import Enum


class Direction(Enum):
    """8-way movement vectors plus STAY, as ``(d_row, d_col)`` offsets.

    Row increases downward, so NORTH decreases the row index.
    """

    N = (-1, 0)
    NE = (-1, 1)
    E = (0, 1)
    SE = (1, 1)
    S = (1, 0)
    SW = (1, -1)
    W = (0, -1)
    NW = (-1, -1)
    STAY = (0, 0)


class AgentRole(str, Enum):
    """The two autonomous agents in the pursuit."""

    COP = "cop"
    THIEF = "thief"


class ActionType(str, Enum):
    """The kinds of action an agent may take on its turn."""

    MOVE = "move"
    PLACE_BARRIER = "place_barrier"


class SubGameOutcome(str, Enum):
    """Terminal result of a single sub-game.

    ``VOID_TECHNICAL`` marks a sub-game aborted by a technical failure; per the
    brief it scores nothing and must be re-run to reach 6 valid sub-games.
    """

    COP_WINS = "cop_wins"
    THIEF_WINS = "thief_wins"
    DRAW = "draw"
    VOID_TECHNICAL = "void_technical"
