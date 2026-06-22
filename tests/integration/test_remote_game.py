"""Integration: drive a full game across two MCP servers (in-memory transport)."""

from __future__ import annotations

import asyncio

from cop_thief.constants import SubGameOutcome
from cop_thief.orchestrator import RemoteGameController, run_remote_game
from cop_thief.servers import CopServer, ThiefServer


def _targets():
    return CopServer().app, ThiefServer().app


def test_remote_game_completes_over_mcp(small_config):
    cop_app, thief_app = _targets()
    result = run_remote_game(small_config, cop_app, thief_app)
    assert len(result.sub_games) == small_config.num_games
    assert all(s.outcome is not SubGameOutcome.VOID_TECHNICAL for s in result.sub_games)


def test_remote_totals_match_sub_game_sums(small_config):
    cop_app, thief_app = _targets()
    result = run_remote_game(small_config, cop_app, thief_app)
    assert result.cop_total == sum(s.cop_score for s in result.sub_games)
    assert result.thief_total == sum(s.thief_score for s in result.sub_games)


def test_remote_transcript_is_natural_language(small_config):
    cop_app, thief_app = _targets()
    result = asyncio.run(
        RemoteGameController(small_config, cop_app, thief_app).play_game()
    )
    messages = [m for rec in result.sub_games for m in rec.transcript]
    assert messages, "expected free-NL messages exchanged over MCP"
    assert all(not any(ch.isdigit() for ch in m) for m in messages)  # KPI K1
