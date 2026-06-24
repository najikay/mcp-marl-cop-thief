"""A per-role roster of 3 strategy-variant agents (game = 3 matches).

Match ``i`` is played by ``agent(i)``. Variants currently differ by exploration
rate (a deliberate hook for future Angel/Devil + game-theoretic specialisation).
"""

from __future__ import annotations

from cop_thief.domain.constants import AgentRole
from cop_thief.domain.strategy.qtable import QTableStrategy

_VARIANTS = ("aggressive", "balanced", "defensive")
_EPSILONS = (0.0, 0.05, 0.1)


class AgentRoster:
    """Hold ``size`` strategy variants for one role and serve them per match."""

    def __init__(self, role: AgentRole, size: int = 3) -> None:
        """Build ``size`` Q-learning agents, each with a distinct exploration rate."""
        self.role = role
        self.agents = [QTableStrategy() for _ in range(size)]
        self.labels = list(_VARIANTS[:size])
        for agent, epsilon in zip(self.agents, _EPSILONS[:size], strict=False):
            agent.epsilon = epsilon

    def agent(self, index: int) -> QTableStrategy:
        """Return the strategy for match ``index`` (wraps around if needed)."""
        return self.agents[index % len(self.agents)]

    def __len__(self) -> int:
        return len(self.agents)
