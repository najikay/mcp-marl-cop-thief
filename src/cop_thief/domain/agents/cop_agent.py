"""CopAgent — the pursuer. May place barriers; narrates pursuit intent."""

from __future__ import annotations

from ...constants import ActionType, AgentRole
from ..action import Action
from ..nl import NLEncoder
from ..strategy import BaseStrategy
from .base_agent import BaseAgent


class CopAgent(BaseAgent):
    """The Cop: closes distance and reports the result at game end."""

    def __init__(self, strategy: BaseStrategy, encoder: NLEncoder | None = None) -> None:
        super().__init__(AgentRole.COP, strategy, encoder)

    def narrate(self, action: Action) -> str:
        """Pursuit-flavoured free-NL narration."""
        if action.kind is ActionType.PLACE_BARRIER:
            return "Cop: I drop a barrier here to cut off your escape."
        return f"Cop: closing in, stepping {action.direction.name} toward you."
