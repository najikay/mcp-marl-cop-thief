"""BaseStrategy — abstract decision policy mapping a state to a legal action."""

from __future__ import annotations

from abc import ABC, abstractmethod

from ...constants import AgentRole
from ..action import Action
from ..board_state import BoardState
from ..nl import BeliefUpdate
from ..rules import RulesEngine


class BaseStrategy(ABC):
    """Abstract base: subclasses turn a perceived state into a legal action."""

    @abstractmethod
    def choose_action(
        self,
        state: BoardState,
        role: AgentRole,
        rules: RulesEngine,
        belief: BeliefUpdate | None = None,
    ) -> Action:
        """Return a rules-legal :class:`Action` for ``role`` given ``state``.

        ``belief`` carries what the agent inferred from the opponent's last
        natural-language message; full-observability strategies may ignore it.
        """
        raise NotImplementedError
