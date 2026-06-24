"""Stateful per-role strategy resolver: Angel–Devil minimax planner variants.

Each ``request_move`` is answered by a depth-limited alpha-beta planner (game
theory) whose Cop action set includes walling its own cell (Conway 'Devil' move),
so barriers and herding-to-trap emerge from search — no hand-coded barrier rule.
The sub-game ``variant`` index selects one of three planner profiles, giving the
six sub-games distinct, principled behaviour.
"""

from __future__ import annotations

from cop_thief.domain.constants import ActionType, AgentRole
from cop_thief.domain.move_language import encode_barrier, encode_move
from cop_thief.domain.strategy.evaluation import Evaluator
from cop_thief.domain.strategy.minimax import MinimaxPlanner
from cop_thief.domain.strategy.roster import VARIANT_LABELS
from cop_thief.servers.tools.move_tool import build_state

# (weights, depth) per variant: aggressive (deep, proximity) / balanced / defensive (containment).
_VARIANTS = (
    ((1.2, 0.5, 0.4, 0.1), 4),
    ((1.0, 0.6, 0.4, 0.1), 3),
    ((0.7, 1.0, 0.6, 0.2), 3),
)


def _default_planners() -> list[MinimaxPlanner]:
    """Build the three variant planners (one Evaluator + depth each)."""
    return [MinimaxPlanner(Evaluator(weights), depth) for weights, depth in _VARIANTS]


class StrategyResolver:
    """Resolve a move via a per-variant Angel–Devil minimax planner."""

    def __init__(self, planners: list[MinimaxPlanner] | None = None) -> None:
        """Hold the variant planners; build the three defaults if unset."""
        self._planners = planners or _default_planners()

    def label(self, role: AgentRole, variant: int) -> str:
        """Return the variant's human label (aggressive / balanced / defensive)."""
        return VARIANT_LABELS[variant % len(VARIANT_LABELS)]

    def resolve(self, observation: dict) -> str:
        """Plan the sub-game variant's action and return it as treaty prose."""
        state, role, pos = build_state(observation)
        planner = self._planners[int(observation.get("variant", 0)) % len(self._planners)]
        action_type, target = planner.best_action(state)
        if action_type is ActionType.PLACE_BARRIER:
            return encode_barrier(role)
        return encode_move(role, pos, target)
