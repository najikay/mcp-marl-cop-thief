"""CopThiefSDK — the one and only entrypoint to all domain logic.

Consumers (CLI, MCP servers, GUI, tests) import *only* this class; they hold no
business logic themselves (PRD §E3, PLAN §2.4). The SDK wires the domain core
to the infrastructure (gatekeeper, LLM) via dependency injection.
"""

from __future__ import annotations

from ..config import ConfigManager
from ..config.models import GameConfig
from ..domain.agents import CopAgent, ThiefAgent
from ..domain.nl import BeliefUpdate, NLEncoder, NLParser
from ..domain.reporting import BonusReport, InternalReport
from ..domain.strategy import BaseStrategy, BeliefHeuristicStrategy, HeuristicStrategy
from ..infra import ApiGatekeeper, LLMClient, make_llm_client
from ..orchestrator import (
    BonusSeriesController,
    BonusSeriesResult,
    GameLoopController,
    GameResult,
    GroupSide,
)


class CopThiefSDK:
    """Single facade over configuration, orchestration and reporting."""

    def __init__(
        self,
        config: GameConfig | None = None,
        gatekeeper: ApiGatekeeper | None = None,
        llm: LLMClient | None = None,
        strategy_factory: type[BaseStrategy] = HeuristicStrategy,
        partial_observability: bool = False,
    ) -> None:
        self._config = config or ConfigManager().load()
        self._gatekeeper = gatekeeper or ApiGatekeeper()
        self._llm = llm or make_llm_client()
        self._strategy_factory = strategy_factory
        self._partial = partial_observability
        self._encoder = NLEncoder()

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
        return GameLoopController(self._config, self.build_cop(), self.build_thief()).play_game()

    def build_cop(self) -> CopAgent:
        """Construct a Cop agent (belief-driven when partial observability is on)."""
        return CopAgent(self._strategy(), self._encoder, self._parser())

    def build_thief(self) -> ThiefAgent:
        """Construct a Thief agent (belief-driven when partial observability is on)."""
        return ThiefAgent(self._strategy(), self._encoder, self._parser())

    def _strategy(self) -> BaseStrategy:
        return BeliefHeuristicStrategy() if self._partial else self._strategy_factory()

    def _parser(self) -> NLParser | None:
        if not self._partial:
            return None
        return NLParser(llm=self._llm, gatekeeper=self._gatekeeper)

    def make_side(
        self,
        name: str,
        github_repo: str,
        cop_mcp_url: str,
        thief_mcp_url: str,
        students: list[str] | None = None,
    ) -> GroupSide:
        """Describe this system as one competing group in a bonus series."""
        return GroupSide(
            name=name,
            github_repo=github_repo,
            cop_mcp_url=cop_mcp_url,
            thief_mcp_url=thief_mcp_url,
            cop_factory=self.build_cop,
            thief_factory=self.build_thief,
            students=students or [],
        )

    def run_bonus_series(self, side_a: GroupSide, side_b: GroupSide) -> BonusSeriesResult:
        """Play a full role-swap bonus series between two groups."""
        return BonusSeriesController(self._config, side_a, side_b).play_series()

    def build_bonus_report(
        self,
        series: BonusSeriesResult,
        side_a: GroupSide,
        side_b: GroupSide,
        mutual_agreement: bool = True,
    ) -> BonusReport:
        """Assemble the inter-group bonus report from a played series."""
        return BonusReport(
            group_1=side_a.name,
            group_2=side_b.name,
            github_repo_group_1=side_a.github_repo,
            github_repo_group_2=side_b.github_repo,
            mcp_url_group_1_cop=side_a.cop_mcp_url,
            mcp_url_group_1_thief=side_a.thief_mcp_url,
            mcp_url_group_2_cop=side_b.cop_mcp_url,
            mcp_url_group_2_thief=side_b.thief_mcp_url,
            sub_games=series.to_sub_game_dicts(),
            totals_by_group=series.totals_by_group,
            mutual_agreement=mutual_agreement,
            students_group_1=side_a.students,
            students_group_2=side_b.students,
        )

    def parse_message(self, text: str) -> BeliefUpdate:
        """Parse an opponent's free-text message into an actionable belief.

        Uses the configured LLM through the gatekeeper, falling back to the
        offline heuristic parser when no provider is wired.
        """
        parser = NLParser(llm=self._llm, gatekeeper=self._gatekeeper)
        return parser.parse(text)

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
