"""Angel–Devil leaf evaluation and terminal scoring for the minimax planner.

The value is **cop-signed** (higher = better for the Cop) so the same number drives
a zero-sum minimax: the Cop maximizes, the Thief minimizes. Terminal scores favour
*sooner* wins (``WIN - turns``) so the policy presses for progress and never stalls.
"""

from __future__ import annotations

from collections.abc import Sequence

from cop_thief.domain.constants import AgentRole
from cop_thief.domain.state import DecPomdpGameState
from cop_thief.domain.strategy.features import feature_vector

WIN = 1000.0
_DEFAULT_WEIGHTS: tuple[float, ...] = (1.0, 0.6, 0.4, 0.1)


class Evaluator:
    """Linear cop-positive evaluation plus zero-sum terminal scoring."""

    def __init__(self, weights: Sequence[float] = _DEFAULT_WEIGHTS, max_moves: int = 25) -> None:
        """Bind the feature weights and the sub-game move cap."""
        self.weights = tuple(float(w) for w in weights)
        self._max_moves = max_moves

    def terminal_value(self, state: DecPomdpGameState) -> float | None:
        """Return a cop-signed terminal score, or None if the sub-game continues."""
        if state.cop_pos == state.thief_pos:
            return WIN - state.turn_counter
        if state.turn_role is AgentRole.THIEF and not state.legal_moves(AgentRole.THIEF):
            return WIN - state.turn_counter
        if state.turn_role is AgentRole.COP and not state.legal_moves(AgentRole.COP):
            return -WIN + state.turn_counter
        if state.turn_counter >= self._max_moves:
            return -WIN + state.turn_counter
        return None

    def value(self, state: DecPomdpGameState) -> float:
        """Return the linear feature value of a non-terminal leaf (cop-positive)."""
        return sum(w * f for w, f in zip(self.weights, feature_vector(state), strict=True))
