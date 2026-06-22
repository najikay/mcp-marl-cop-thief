"""Encapsulated state-management services behind the SDK facade.

``MatchCoordinator`` owns the progression of the 6-sub-game match (3 as Cop, 3
as Thief — the asymmetric dual-role mandate), enforces immutable transitions,
and evaluates terminal conditions.
"""

from __future__ import annotations

from cop_thief.domain.constants import ActionType, AgentRole, SubGameOutcome
from cop_thief.domain.state import DecPomdpGameState
from cop_thief.sdk.exceptions import IllegalGameMutationError


class MatchCoordinator:
    """Drive role alternation, immutable steps and terminal evaluation."""

    def __init__(
        self,
        num_games: int = 6,
        max_moves: int = 25,
        cop_games: int = 3,
        token_tracker=None,
    ) -> None:
        """Configure match length and the Cop/Thief split."""
        self.num_games = num_games
        self.max_moves = max_moves
        self.cop_games = cop_games
        self._tracker = token_tracker
        self.current_sub_game = 0
        self.current_role = self._role_for(0)

    def _role_for(self, index: int) -> AgentRole:
        """Return the role we play in sub-game ``index`` (Cop first, then Thief)."""
        return AgentRole.COP if index < self.cop_games else AgentRole.THIEF

    def schedule(self) -> list[AgentRole]:
        """Return the full role schedule across all sub-games."""
        return [self._role_for(i) for i in range(self.num_games)]

    def reset(self) -> None:
        """Reset the match to the first sub-game."""
        self.current_sub_game = 0
        self.current_role = self._role_for(0)

    def advance_sub_game(self) -> None:
        """Move to the next sub-game, updating the active role."""
        self.current_sub_game += 1
        self.current_role = self._role_for(self.current_sub_game)

    def execute_agent_step(
        self, state: DecPomdpGameState, action: ActionType, target: tuple
    ) -> DecPomdpGameState:
        """Apply one immutable action for the active role; never mutate input.

        Raises ``IllegalGameMutationError`` if ``state`` is not a valid
        immutable game state.
        """
        if not isinstance(state, DecPomdpGameState):
            raise IllegalGameMutationError("state must be a DecPomdpGameState")
        return state.apply_action(self.current_role, action, target)

    def evaluate_terminal_condition(
        self, state: DecPomdpGameState
    ) -> SubGameOutcome | None:
        """Return the sub-game outcome, or ``None`` if play continues."""
        if state.cop_pos == state.thief_pos:
            return SubGameOutcome.COP_WINS
        if state.turn_counter >= self.max_moves:
            return SubGameOutcome.THIEF_WINS
        return None

    def economics(self) -> dict:
        """Return live token economics from the tracker (empty if unset)."""
        return self._tracker.get_current_economics() if self._tracker else {}
