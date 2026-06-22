"""Integration tests: a full game end-to-end and the internal report."""

from __future__ import annotations

import json

from cop_thief.constants import SubGameOutcome
from cop_thief.domain.agents import CopAgent, ThiefAgent
from cop_thief.domain.reporting import InternalReport
from cop_thief.domain.strategy import HeuristicStrategy
from cop_thief.orchestrator import GameLoopController


def _controller(config):
    cop = CopAgent(HeuristicStrategy())
    thief = ThiefAgent(HeuristicStrategy())
    return GameLoopController(config, cop, thief)


def test_full_game_produces_six_valid_sub_games(small_config):
    result = _controller(small_config).play_game()
    assert len(result.sub_games) == small_config.num_games
    assert all(s.outcome is not SubGameOutcome.VOID_TECHNICAL for s in result.sub_games)


def test_totals_match_sub_game_sums(small_config):
    result = _controller(small_config).play_game()
    assert result.cop_total == sum(s.cop_score for s in result.sub_games)
    assert result.thief_total == sum(s.thief_score for s in result.sub_games)


def test_internal_report_schema_is_valid_json(small_config):
    result = _controller(small_config).play_game()
    report = InternalReport(
        group_name="Team-Test",
        github_repo="https://github.com/x/y",
        cop_mcp_url="http://localhost:8001",
        thief_mcp_url="http://localhost:8002",
        result=result,
    )
    data = json.loads(report.to_json())
    assert data["group_name"] == "Team-Test"
    assert set(data["totals"]) == {"cop", "thief"}
    assert len(data["sub_games"]) == small_config.num_games


def test_game_is_deterministic_under_seed(small_config):
    a = _controller(small_config).play_game()
    b = _controller(small_config).play_game()
    assert (a.cop_total, a.thief_total) == (b.cop_total, b.thief_total)
