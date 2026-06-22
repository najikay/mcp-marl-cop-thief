"""CopThiefSDK — the one and only entrypoint to all domain logic.

Consumers (CLI, MCP servers, GUI, tests) import *only* this class; they hold no
business logic themselves (PRD §E3, PLAN §2.4). The SDK wires the domain core
to the infrastructure (gatekeeper, LLM) via dependency injection.
"""

from __future__ import annotations

from ..auth import GmailReporter
from ..config import ConfigManager
from ..config.models import GameConfig
from ..domain.agents import CopAgent, ThiefAgent
from ..domain.nl import BeliefUpdate, NLEncoder, NLParser
from ..domain.reporting import BonusReport, InternalReport
from ..domain.strategy import BaseStrategy, BeliefHeuristicStrategy, HeuristicStrategy
from ..domain.turn_advisor import propose_turn as _propose_turn
from ..infra import ApiGatekeeper, LLMClient, make_llm_client
from ..orchestrator import (
    BonusSeriesController,
    BonusSeriesResult,
    GameLoopController,
    GameResult,
    GroupSide,
    run_remote_game,
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

    def play_remote_game(
        self, cop_target, thief_target, cop_token=None, thief_token=None
    ) -> GameResult:
        """Drive a full game across two remote MCP servers (URLs or apps)."""
        return run_remote_game(self._config, cop_target, thief_target, cop_token, thief_token)

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
        return BonusReport.from_sides(series, side_a, side_b, mutual_agreement)

    def propose_turn(self, self_cell: tuple[int, int], role: str, belief=None) -> dict:
        """Decide one MCP turn from the agent's own cell and current belief."""
        return _propose_turn(self._config, self._encoder, tuple(self_cell), role, belief)

    def send_report(self, report, gmail_service, recipient: str | None = None) -> dict:
        """Email a report's JSON body via the Gmail API (one email, JSON only)."""
        reporter = GmailReporter(gmail_service, self._gatekeeper, recipient)
        return reporter.send_report(report.to_json())

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
