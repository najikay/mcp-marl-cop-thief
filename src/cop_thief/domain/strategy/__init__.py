"""Strategy stack: tabular Q-learning (Tier-1) with geometric fallbacks."""

from cop_thief.domain.strategy.heuristic import pursuit_target
from cop_thief.domain.strategy.qtable import QTableStrategy
from cop_thief.domain.strategy.roster import AgentRoster

__all__ = ["QTableStrategy", "pursuit_target", "AgentRoster"]
