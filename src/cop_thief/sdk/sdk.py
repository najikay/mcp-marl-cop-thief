"""CopThiefSDK — the one and only entrypoint to all domain logic.

Consumers (CLI, MCP servers, GUI, tests) import *only* this class; they hold no
business logic themselves (PRD §E3, PLAN §2.4). The SDK wires the domain core
to the infrastructure (gatekeeper, LLM) via dependency injection.
"""

from __future__ import annotations

from ..config import ConfigManager
from ..config.models import GameConfig
from ..domain.agents import CopAgent, ThiefAgent
from ..domain.reporting import InternalReport
from ..domain.strategy import BaseStrategy, HeuristicStrategy
from ..infra import ApiGatekeeper, LLMClient, make_llm_client
from ..orchestrator import GameLoopController, GameResult


class CopThiefSDK:
    """Single facade over configuration, orchestration and reporting."""

    def __init__(
        self,
        config: GameConfig | None = None,
        gatekeeper: ApiGatekeeper | None = None,
        llm: LLMClient | None = None,
        strategy_factory: type[BaseStrategy] = HeuristicStrategy,
    ) -> None:
        self._config = config or ConfigManager().load()
        self._gatekeeper = gatekeeper or ApiGatekeeper()
        self._llm = llm or make_llm_client()
        self._strategy_factory = strategy_factory

    @classmethod
    def from_config_path(cls, path: str | None = None) -> CopThiefSDK:
        """Build an SDK from a config file path (used by the CLI)."""
        return cls(config=ConfigManager(path).load())

    @property
    def config(self) -> GameConfig:
        """The validated game configuration in use."""
        return self._config

    def play_game(self) -> GameResult:
        """Play a full game (``num_games`` valid sub-games) and return totals."""
        cop = CopAgent(self._strategy_factory())
        thief = ThiefAgent(self._strategy_factory())
        return GameLoopController(self._config, cop, thief).play_game()

    def build_internal_report(
        self,
        result: GameResult,
        group_name: str,
        github_repo: str,
        cop_mcp_url: str,
        thief_mcp_url: str,
    ) -> InternalReport:
        """Assemble the internal game JSON report from a played game."""
        return InternalReport(
            group_name=group_name,
            github_repo=github_repo,
            cop_mcp_url=cop_mcp_url,
            thief_mcp_url=thief_mcp_url,
            result=result,
        )
