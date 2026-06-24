"""TDD: ChallengeRunner per-leg cross-host routing + bonus report assembly."""

from __future__ import annotations

from cop_thief.orchestrator.challenge_runner import ChallengeRunner
from cop_thief.orchestrator.reconcile import canonical_hash
from cop_thief.servers.tools.move_tool import resolve_move


def _runner() -> ChallengeRunner:
    """A runner whose opponent AND our resolver are the fast deterministic geometry."""
    return ChallengeRunner("NajAmjad", "Team-Beta", their_cop=resolve_move,
                           their_thief=resolve_move, our_resolver=resolve_move, turn_delay=0.0)


def test_challenge_runs_six_subgames_over_both_legs() -> None:
    """A full challenge yields 6 sub-games split across the HOME and AWAY legs."""
    report = _runner().run()
    assert report["report_type"] == "bonus_game"
    assert len(report["sub_games"]) == 6
    assert {sg["venue"] for sg in report["sub_games"]} == {"home", "away"}
    assert report["groups"] == {"ours": "NajAmjad", "opponent": "Team-Beta"}


def test_challenge_report_hash_and_result() -> None:
    """The report hashes the canonical sub_games and resolves a final result."""
    report = _runner().run()
    assert report["agreement_sha256"] == canonical_hash(report["sub_games"])
    assert report["final_result"] in {"ours", "opponent", "tie"}
    assert report["mutual_agreement"] is None  # pending the opponent's report


def test_home_leg_is_cop_away_leg_is_thief() -> None:
    """Per-leg routing assigns us Cop on HOME (1-3) and Thief on AWAY (4-6)."""
    sub_games = _runner().run()["sub_games"]
    assert all(sg["our_role"] == "cop" for sg in sub_games[:3])
    assert all(sg["our_role"] == "thief" for sg in sub_games[3:])
