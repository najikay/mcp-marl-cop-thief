"""The single-entrypoint business facade (Guidelines §4.1/§5.2).

Every consumer (CLI, GUI, MCP tool handlers, tests) talks to the domain only
through :class:`CopThiefSDK`. The facade wires configuration, the API gatekeeper
and the match coordinator, and inherits adversarial tactics from
:class:`WarfareOperationsMixin`.
"""

from __future__ import annotations

from cop_thief.config import ConfigManager, get_config_manager
from cop_thief.domain.constants import ActionType
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
        except Exception as exc:  # noqa: BLE001 - re-raised as a typed SDK error
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
