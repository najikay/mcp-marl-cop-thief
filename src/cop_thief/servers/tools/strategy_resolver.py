"""Stateful per-role strategy resolver: risk-tunable Angel–Devil minimax variants.

Each ``request_move`` is answered by a minimax/expectimax planner (game theory) whose
Cop action set includes walling its own cell (Conway 'Devil' move). An online
``OpponentModel`` watches the opponent's moves across the session and lowers our
pessimism toward expectimax only as far as the opponent proves exploitable; each
variant's ``risk`` controls how much it trusts that signal (defensive = pure minimax).
"""

from __future__ import annotations

from cop_thief.domain.constants import ActionType, AgentRole
from cop_thief.domain.move_language import encode_barrier, encode_move
from cop_thief.domain.strategy.evaluation import Evaluator
from cop_thief.domain.strategy.minimax import MinimaxPlanner
from cop_thief.domain.strategy.opponent import OpponentModel, opponent_was_rational
from cop_thief.domain.strategy.roster import VARIANT_LABELS
from cop_thief.servers.tools.move_tool import build_state

# (weights, depth, risk): aggressive (exploit) / balanced / defensive (pure minimax, safe).
_VARIANTS = (
    ((1.2, 0.5, 0.4, 0.1), 3, 1.0),
    ((1.0, 0.6, 0.4, 0.1), 3, 0.5),
    ((0.7, 1.0, 0.6, 0.2), 2, 0.0),
)


class StrategyResolver:
    """Resolve a move via a risk-tunable minimax planner with online opponent modelling."""

    def __init__(self, variants=None) -> None:
        """Build the variant (planner, risk) pairs and a fresh opponent model."""
        self._variants = variants or [
            (MinimaxPlanner(Evaluator(w), depth), risk) for w, depth, risk in _VARIANTS
        ]
        self._model = OpponentModel()
        self._last: dict | None = None

    def label(self, role: AgentRole, variant: int) -> str:
        """Return the variant's human label (aggressive / balanced / defensive)."""
        return VARIANT_LABELS[variant % len(VARIANT_LABELS)]

    def _learn(self, observation: dict) -> None:
        """Update the opponent model from its last move (skip on reset / first call)."""
        last, self._last = self._last, observation
        if last is None or observation.get("turn", 0) <= last.get("turn", 0):
            return
        self._model.observe(opponent_was_rational(observation["role"], last, observation))

    def resolve(self, observation: dict) -> str:
        """Plan the variant's action (pessimism adapted to the opponent) as treaty prose."""
        self._learn(observation)
        state, role, pos = build_state(observation)
        planner, risk = self._variants[int(observation.get("variant", 0)) % len(self._variants)]
        pessimism = 1.0 - risk * (1.0 - self._model.pessimism())
        action_type, target = planner.best_action(state, pessimism)
        if action_type is ActionType.PLACE_BARRIER:
            return encode_barrier(role)
        return encode_move(role, pos, target)
