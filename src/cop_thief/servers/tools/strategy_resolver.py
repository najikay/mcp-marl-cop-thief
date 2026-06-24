"""Stateful per-role strategy resolver: 3-variant roster + Q-policy for live play.

Held by an MCP server for the whole session, so each role's ``AgentRoster`` (and
its Q-tables) persist across ``request_move`` calls and across the 6 sub-games. A
sub-game's ``variant`` index selects the agent (aggressive / balanced / defensive),
giving the six sub-games distinct behaviour. Move selection is the variant's
epsilon-greedy Q-policy with the Conway-aware geometry as the Tier-2 fallback; the
Cop's barrier policy (shared ``encode_action``) still applies.
"""

from __future__ import annotations

from cop_thief.domain.constants import AgentRole
from cop_thief.domain.move_language import encode_move
from cop_thief.domain.strategy.heuristic import pursuit_target
from cop_thief.domain.strategy.roster import AgentRoster
from cop_thief.servers.tools.move_tool import build_state


class StrategyResolver:
    """Resolve a move via a persistent per-role roster of Q-learning variants."""

    def __init__(self, rosters: dict | None = None) -> None:
        """Hold one ``AgentRoster`` (3 variants) per role; build defaults if unset."""
        self._rosters = rosters or {role: AgentRoster(role) for role in AgentRole}

    def label(self, role: AgentRole, variant: int) -> str:
        """Return the variant's human label (aggressive / balanced / defensive)."""
        roster = self._rosters[role]
        return roster.labels[variant % len(roster)]

    def resolve(self, observation: dict) -> str:
        """Pick the sub-game's variant agent and return its action as treaty prose."""
        state, role, pos = build_state(observation)
        agent = self._rosters[role].agent(int(observation.get("variant", 0)))
        target = agent.select_target(state, role, fallback=pursuit_target)
        return encode_move(role, pos, target)
