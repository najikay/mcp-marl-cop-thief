"""Unit tests for token-budget tracking."""

from __future__ import annotations

from cop_thief.config.models import GameConfig
from cop_thief.infra import MeteredLLMClient, MockLLMClient, TokenTracker
from cop_thief.infra.token_tracker import estimate_tokens
from cop_thief.sdk import CopThiefSDK


def test_estimate_tokens_is_length_based():
    assert estimate_tokens("") == 1  # floor of one token
    assert estimate_tokens("a" * 40) == 10


def test_tracker_accumulates_and_totals():
    tracker = TokenTracker()
    tracker.record(10, 5)
    tracker.record(4, 1)
    assert tracker.calls == 2
    assert tracker.total_tokens == 20
    assert tracker.usage()["input_tokens"] == 14


def test_estimated_cost_uses_rates():
    tracker = TokenTracker(input_tokens=1000, output_tokens=2000)
    assert tracker.estimated_cost(usd_per_1k_input=0.5, usd_per_1k_output=1.0) == 2.5


def test_metered_client_records_each_call():
    client = MeteredLLMClient(MockLLMClient())
    client.complete("hello there")
    client.complete("another prompt")
    assert client.usage()["calls"] == 2
    assert client.usage()["total_tokens"] > 0


def test_sdk_reports_token_usage_after_partial_game():
    config = GameConfig.from_dict(
        {
            "version": "1.0.0",
            "grid_size": [2, 2],
            "max_moves": 5,
            "num_games": 2,
            "max_barriers": 5,
            "random_start": True,
            "seed": 7,
            "scoring": {"cop_win": 20, "thief_win": 10, "cop_loss": 5, "thief_loss": 5},
        }
    )
    sdk = CopThiefSDK(config=config, partial_observability=True)
    sdk.play_game()
    assert sdk.token_usage()["calls"] > 0  # belief parsing consumed LLM calls
