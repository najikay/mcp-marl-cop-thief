"""CaptureMixin — single concern: detect when the Cop has caught the Thief."""

from __future__ import annotations

from ..board_state import BoardState


class CaptureMixin:
    """Same-cell capture detection. Provides exactly one concern."""

    def is_capture(self, state: BoardState) -> bool:
        """True when the Cop occupies the exact cell of the Thief."""
        return state.cop == state.thief
