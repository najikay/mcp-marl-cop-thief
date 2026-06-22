"""Unit tests for the CopThiefSDK single entrypoint."""

from __future__ import annotations

import json

from cop_thief.sdk import CopThiefSDK


def test_sdk_plays_full_game(small_config):
    sdk = CopThiefSDK(config=small_config)
    result = sdk.play_game()
    assert len(result.sub_games) == small_config.num_games


def test_sdk_builds_valid_report(small_config):
    sdk = CopThiefSDK(config=small_config)
    result = sdk.play_game()
    report = sdk.build_internal_report(
        result,
        group_name="Team-Test",
        github_repo="https://github.com/x/y",
        cop_mcp_url="http://localhost:8001",
        thief_mcp_url="http://localhost:8002",
    )
    data = json.loads(report.to_json())
    assert data["group_name"] == "Team-Test"
    assert set(data["totals"]) == {"cop", "thief"}


def test_sdk_exposes_config(small_config):
    sdk = CopThiefSDK(config=small_config)
    assert sdk.config.num_games == small_config.num_games
