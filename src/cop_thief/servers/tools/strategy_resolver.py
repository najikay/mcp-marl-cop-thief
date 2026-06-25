"""Per-role strategy resolver: risk-tunable adaptive variants, or deterministic tournament minimax.

**Adaptive (our standing default, ``game.deterministic_moves`` off):** the 3 risk variants +
the online ``OpponentModel`` that lowers pessimism against an exploitable opponent. **Tournament
mode** (``game.deterministic_moves`` on) makes each ``request_move`` a **pure function of the
observation** — a single greedy minimax (pessimism 1.0, no exploration, no history) — so two
engines + one seed replay byte-identical sub_games (the inter-group hash agreement, K3); enable
it only when an opponent negotiates byte-agreement. Barriers toggle via ``game.barriers_enabled``.
"""

from __future__ import annotations

from cop_thief.config import get_config_manager
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
    """Resolve a move — deterministic (tournament) or risk-tunable with opponent modelling."""

    def __init__(self, variants=None, deterministic=None, barriers=None) -> None:
        """Read mode/barrier toggles from config (overridable) and build the planner(s)."""
        game = get_config_manager().setup.game
        self._deterministic = game.deterministic_moves if deterministic is None else deterministic
        barr = game.barriers_enabled if barriers is None else barriers
        if self._deterministic:
            self._planner = MinimaxPlanner(Evaluator(), depth=3, barriers=barr)
        else:
            self._variants = variants or [
                (MinimaxPlanner(Evaluator(w), depth, barriers=barr), risk) for w, depth, risk in _VARIANTS
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
        """Plan the move and return it as treaty prose (deterministic by default)."""
        state, role, pos = build_state(observation)
        if self._deterministic:
            action_type, target = self._planner.best_action(state, pessimism=1.0)
        else:
            self._learn(observation)
            planner, risk = self._variants[int(observation.get("variant", 0)) % len(self._variants)]
            pessimism = 1.0 - risk * (1.0 - self._model.pessimism())
            action_type, target = planner.best_action(state, pessimism)
        if action_type is ActionType.PLACE_BARRIER:
            return encode_barrier(role, pos, target)
        return encode_move(role, pos, target)
