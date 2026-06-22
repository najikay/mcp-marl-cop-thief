"""The single-entrypoint business facade (Guidelines §4.1/§5.2).

Every consumer (CLI, GUI, MCP tool handlers, tests) talks to the domain only
through :class:`CopThiefSDK`. The facade wires configuration, the API gatekeeper
and the match coordinator, and inherits adversarial tactics from
:class:`WarfareOperationsMixin`.
"""

from __future__ import annotations

from pydantic import ValidationError

from cop_thief.config import (
    ConfigManager,
    ConfigurationVersionError,
    get_config_manager,
)
from cop_thief.domain.constants import ActionType, AgentRole
from cop_thief.domain.state import DecPomdpGameState
from cop_thief.infra.gatekeeper import ApiGatekeeper, TokenTracker
from cop_thief.sdk.exceptions import SdkInitializationError
from cop_thief.sdk.services import MatchCoordinator
from cop_thief.sdk.warfare import WarfareOperationsMixin


class CopThiefSDK(WarfareOperationsMixin):
    """Single entrypoint to all business logic."""

    def __init__(self, config_dir=None) -> None:
        """Instantiate config, gatekeeper and match coordinator (fail fast)."""
        try:
            self._config = ConfigManager(config_dir) if config_dir else get_config_manager()
        except (OSError, ValueError, ConfigurationVersionError, ValidationError) as exc:
            raise SdkInitializationError(str(exc)) from exc
        setup = self._config.setup
        self._tracker = TokenTracker(
            usage_file=setup.token_budget.usage_file, config_manager=self._config
        )
        self._gatekeeper = ApiGatekeeper(
            self._config.rate_limits, setup.llm_routing, token_tracker=self._tracker
        )
        self._coordinator = MatchCoordinator(
            num_games=setup.game.num_games,
            max_moves=setup.game.max_moves,
            token_tracker=self._tracker,
        )

    def initialize_match(self) -> dict:
        """Reset the match and return its role schedule and current position."""
        self._coordinator.reset()
        return {
            "num_games": self._coordinator.num_games,
            "cop_games": self._coordinator.cop_games,
            "schedule": [role.value for role in self._coordinator.schedule()],
            "current_role": self._coordinator.current_role.value,
            "current_sub_game": self._coordinator.current_sub_game,
        }

    def process_turn(
        self, state: DecPomdpGameState, action: ActionType, target: tuple
    ) -> DecPomdpGameState:
        """Apply one immutable agent action via the coordinator."""
        return self._coordinator.execute_agent_step(state, action, target)

    @property
    def current_role(self) -> AgentRole:
        """Our assigned role for the active sub-game."""
        return self._coordinator.current_role

    @property
    def grid_shape(self) -> tuple[int, int]:
        """Configured board shape as a (rows, cols) tuple."""
        rows, cols = self._config.setup.game.grid_size
        return (rows, cols)

    @property
    def max_moves(self) -> int:
        """Configured maximum moves per sub-game."""
        return self._config.setup.game.max_moves

    def evaluate_terminal(self, state: DecPomdpGameState):
        """Delegate terminal evaluation to the match coordinator."""
        return self._coordinator.evaluate_terminal_condition(state)

    def resolve_prose(self, inbound_prose: str, role: AgentRole) -> str:
        """Produce the agent's outgoing natural-language reply for ``role``.

        Placeholder deterministic responder; the Phase-7 NL encoder/parser will
        replace this with belief-driven prose generation via the gatekeeper.
        """
        _ = inbound_prose
        return (
            f"[{role.value}] Acknowledged your message; holding position and "
            "reassessing the grid."
        )

    def public_telemetry(self) -> dict:
        """Return a sanitized agreement view (no secret strategy weights)."""
        econ = self._coordinator.economics()
        return {
            "current_role": self._coordinator.current_role.value,
            "current_sub_game": self._coordinator.current_sub_game,
            "telemetry": {
                "input_accumulated": econ.get("input_accumulated", 0),
                "output_accumulated": econ.get("output_accumulated", 0),
                "estimated_cost_usd": econ.get("estimated_cost_usd", 0.0),
            },
        }

    def generate_canonical_reports(self) -> dict:
        """Return the canonical match record with injected token telemetry."""
        econ = self._coordinator.economics()
        return {
            "schedule": [role.value for role in self._coordinator.schedule()],
            "current_sub_game": self._coordinator.current_sub_game,
            "telemetry": {
                "input_accumulated": econ.get("input_accumulated", 0),
                "output_accumulated": econ.get("output_accumulated", 0),
                "estimated_cost_usd": econ.get("estimated_cost_usd", 0.0),
                "status": "OK",
            },
        }
