"""BaseAgent — template method ``take_turn`` (perceive → decide → narrate).

An agent perceives the opponent only through natural language: :meth:`observe`
parses an incoming message into a belief, which :meth:`take_turn` feeds to the
strategy. The decision itself is delegated to a :class:`BaseStrategy`; subclasses
supply only the role-specific flavour of their outgoing message.
"""

from __future__ import annotations

from dataclasses import dataclass

from ...constants import ActionType, AgentRole
from ..action import Action
from ..board_state import BoardState
from ..nl import BeliefUpdate, NLEncoder, NLParser
from ..rules import RulesEngine
from ..strategy import BaseStrategy


@dataclass(frozen=True)
class Turn:
    """The product of a turn: the chosen action and its free-NL narration."""

    action: Action
    message: str


class BaseAgent:
    """A role-bound player. ``take_turn`` is a template method (do not override)."""

    def __init__(
        self,
        role: AgentRole,
        strategy: BaseStrategy,
        encoder: NLEncoder | None = None,
        parser: NLParser | None = None,
    ) -> None:
        self.role = role
        self._strategy = strategy
        self._encoder = encoder
        self._parser = parser
        self._belief: BeliefUpdate | None = None

    def observe(self, message: str | None) -> None:
        """Update the belief from an opponent's free-text message (if parsing on)."""
        if self._parser is not None and message:
            self._belief = self._parser.parse(message)

    def reset(self) -> None:
        """Clear the belief at the start of a new sub-game."""
        self._belief = None

    def take_turn(self, state: BoardState, rules: RulesEngine) -> Turn:
        """Perceive the state, decide a legal action, and narrate it as free NL."""
        action = self._strategy.choose_action(state, self.role, rules, self._belief)
        return Turn(action=action, message=self._message(state, action, rules))

    def _message(self, state: BoardState, action: Action, rules: RulesEngine) -> str:
        """Free-NL message: the encoder's prose if wired, else simple narration."""
        if self._encoder is None:
            return self.narrate(action)
        cell = state.cop if self.role is AgentRole.COP else state.thief
        return self._encoder.describe(
            cell, rules.grid.rows, rules.grid.cols, self.role, action.direction
        )

    def narrate(self, action: Action) -> str:
        """Default narration; subclasses add role-specific flavour."""
        if action.kind is ActionType.PLACE_BARRIER:
            return f"{self.role.value}: I seal the lane I'm standing on."
        return f"{self.role.value}: I move {action.direction.name}."
