"""TDD unit tests for the move language, request_move resolver, and SeriesRunner."""

from __future__ import annotations

from unittest import mock

from cop_thief.domain.constants import AgentRole, SubGameOutcome
from cop_thief.domain.move_language import apply_prose, encode_move, parse_target
from cop_thief.domain.state import DecPomdpGameState
from cop_thief.orchestrator.series import SeriesRunner
from cop_thief.servers.tools.move_tool import resolve_move


def test_encode_parse_roundtrip_and_longest_word() -> None:
    prose = encode_move(AgentRole.COP, (2, 2), (1, 3))  # delta (-1,+1) = north-east
    assert "north-east" in prose and "MOVE" in prose
    assert parse_target(prose, (2, 2)) == (1, 3)
    assert parse_target("edges north", (2, 2)) == (1, 2)  # not mis-read as north-east


def test_apply_prose_illegal_holds() -> None:
    state = DecPomdpGameState(cop_pos=(0, 0), thief_pos=(4, 4))
    moved = apply_prose(state, AgentRole.COP, "edges north")  # off-board -> hold
    assert moved.cop_pos == (0, 0)


def test_resolve_move_returns_treaty_prose() -> None:
    obs = {"role": "cop", "grid": [5, 5], "cop": [0, 0], "thief": [4, 4], "barriers": []}
    assert resolve_move(obs).startswith("[INTENT:")


def test_series_one_merged_scored_report() -> None:
    """6 matches, thief-first, ONE merged report with venue/points/totals/final."""
    recorded: list = []
    reporter = mock.Mock()
    reporter.dispatch_payload = mock.Mock(return_value={})
    runner = SeriesRunner(
        cop_provider=resolve_move, thief_provider=resolve_move,
        observer=lambda s, p, i: recorded.append(s), reporter=reporter, turn_delay=0.0,
    )
    report = runner.run_series()
    assert reporter.dispatch_payload.call_count == 1  # ONE merged email
    assert report["report_type"] == "game_report"
    assert len(report["sub_games"]) == 6
    assert set(report["totals"]) == {"ours", "opponent"}
    assert report["final_result"] in {"ours", "opponent", "tie"}
    assert len(report["agreement_sha256"]) == 64
    assert all("our_points" in sg and "venue" in sg for sg in report["sub_games"])
    assert {sg["venue"] for sg in report["sub_games"]} == {"home", "away"}
    assert recorded[0].turn_role is AgentRole.COP  # thief already moved first


def test_play_match_terminates_validly() -> None:
    runner = SeriesRunner(resolve_move, resolve_move, turn_delay=0.0)
    outcome = runner.play_match()
    assert outcome in {
        SubGameOutcome.COP_WINS, SubGameOutcome.THIEF_WINS, SubGameOutcome.THIEF_TRAPPED,
    }
