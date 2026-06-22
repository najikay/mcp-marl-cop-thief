"""TurnMixin — single concern: turn order and the move-count terminal bound."""

from __future__ import annotations

from ...constants import AgentRole
from ..board_state import BoardState


class TurnMixin:
    """Turn arbitration. Provides exactly one concern.

    The Thief moves first by default; turns then alternate. One full round is
    two half-moves (thief then cop), so ``move_count`` counts half-moves.
    """

    def first_mover(self) -> AgentRole:
        """The role that acts first in a sub-game."""
        return AgentRole.THIEF

    def next_mover(self, current: AgentRole) -> AgentRole:
        """Whose turn follows ``current``."""
        return AgentRole.COP if current is AgentRole.THIEF else AgentRole.THIEF

    def moves_exhausted(self, state: BoardState, max_moves: int) -> bool:
        """True once the thief has survived ``max_moves`` full rounds."""
        return state.move_count >= max_moves * 2
