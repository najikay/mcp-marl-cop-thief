"""RulesEngine — composes the four single-concern mixins into one gate.

It answers two questions for the orchestrator: *is this action legal?*
(:meth:`validate`) and *has the sub-game ended?* (:meth:`terminal_check`).
"""

from __future__ import annotations

from ...constants import ActionType, SubGameOutcome
from ..action import Action
from ..board_state import BoardState
from ..grid import Grid
from .barrier_mixin import BarrierMixin
from .capture_mixin import CaptureMixin
from .movement_mixin import MovementMixin
from .turn_mixin import TurnMixin


class RulesEngine(MovementMixin, BarrierMixin, CaptureMixin, TurnMixin):
    """Unified rule gate built from independent mixins (none override others)."""

    def __init__(self, grid: Grid, max_moves: int) -> None:
        self._grid = grid
        self._max_moves = max_moves

    @property
    def grid(self) -> Grid:
        """The board geometry these rules apply to."""
        return self._grid

    def validate(self, state: BoardState, action: Action) -> bool:
        """True if ``action`` is legal in ``state`` for its declared role."""
        if not isinstance(action, Action):
            return False
        if action.kind is ActionType.PLACE_BARRIER:
            return self.is_barrier_legal(action.role, state)
        origin = self._actor_cell(state, action)
        return self.is_move_legal(self._grid, state, origin, action.direction)

    def terminal_check(self, state: BoardState) -> SubGameOutcome | None:
        """Return the outcome if the sub-game is over, else ``None``."""
        if self.is_capture(state):
            return SubGameOutcome.COP_WINS
        if self.moves_exhausted(state, self._max_moves):
            return SubGameOutcome.THIEF_WINS
        return None

    @staticmethod
    def _actor_cell(state: BoardState, action: Action):
        from ...constants import AgentRole

        return state.cop if action.role is AgentRole.COP else state.thief
