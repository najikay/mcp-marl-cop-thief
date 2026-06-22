"""BarrierMixin — single concern: when a barrier placement is allowed.

Only the Cop may place barriers, only while quota remains, and never on a cell
that is already sealed.
"""

from __future__ import annotations

from ...constants import AgentRole
from ..board_state import BoardState


class BarrierMixin:
    """Barrier-placement legality. Provides exactly one concern."""

    def is_barrier_legal(self, role: AgentRole, state: BoardState) -> bool:
        """True if ``role`` may seal its current cell in ``state``."""
        if role is not AgentRole.COP:
            return False
        if state.barriers_left <= 0:
            return False
        return state.cop not in state.barriers
