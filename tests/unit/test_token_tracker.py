"""TDD unit tests for the gatekeeper's TokenTracker ledger (mocked filesystem only).

Scenarios:
1. A corrupt ``token_usage.json`` is tolerated — the tracker recovers and starts clean.
2. Token-accounting math across the DeepSeek + Anthropic per-million ledger rates.
"""

from __future__ import annotations

from pathlib import Path

from cop_thief.infra.gatekeeper import TokenTracker


def test_corrupt_ledger_recovers(tmp_path: Path) -> None:
    """A corrupt token_usage.json is tolerated; the tracker starts clean."""
    ledger = tmp_path / "token_usage.json"
    ledger.write_text("{ this is not valid json", encoding="utf-8")

    tracker = TokenTracker(usage_file=ledger)
    assert tracker.get_current_economics()["turns"] == 0  # recovered, not crashed

    tracker.log_turn("DEEPSEEK", "deepseek-chat", 100, 10)
    assert tracker.get_current_economics()["turns"] == 1


def test_token_accounting_math(tmp_path: Path) -> None:
    """Ledger math: DeepSeek 0.15/0.60 + Anthropic 3.00/15.00 per million."""
    tracker = TokenTracker(usage_file=tmp_path / "u.json")
    tracker.log_turn("DEEPSEEK", "deepseek-chat", 1_000_000, 1_000_000)
    tracker.log_turn("ANTHROPIC", "claude-3-5-sonnet-20241022", 1_000_000, 1_000_000)

    econ = tracker.get_current_economics()
    assert econ["input_accumulated"] == 2_000_000
    assert econ["output_accumulated"] == 2_000_000
    # DeepSeek: 0.15 + 0.60 = 0.75 ; Anthropic: 3.00 + 15.00 = 18.00
    assert econ["estimated_cost_usd"] == round(0.75 + 18.0, 6)
    assert econ["turns"] == 2
