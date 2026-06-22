"""ThiefAgent — the evader. Never places barriers; narrates evasion intent."""

from __future__ import annotations

from ...constants import AgentRole
from ..action import Action
from ..strategy import BaseStrategy
from .base_agent import BaseAgent


class ThiefAgent(BaseAgent):
    """The Thief: opens distance and survives ``max_moves``."""

    def __init__(self, strategy: BaseStrategy) -> None:
        super().__init__(AgentRole.THIEF, strategy)

    def narrate(self, action: Action) -> str:
        """Evasion-flavoured free-NL narration (may bluff in later versions)."""
        return f"Thief: slipping away {action.direction.name}, you won't reach me."
