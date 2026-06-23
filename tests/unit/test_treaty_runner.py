"""TDD unit tests for the Section 12 inter-group treaty orchestrator."""

from __future__ import annotations

from unittest import mock

import pytest

from cop_thief.config.aux_models import NetworkConfig
from cop_thief.domain.constants import SubGameOutcome
from cop_thief.orchestrator import treaty_runner as tr
from cop_thief.reporting import GmailApiReporter, SubmissionSafetyException, SubmissionSafetyGuard


def test_role_schedule_section_12_1() -> None:
    sched = tr.role_schedule()
    assert sched[:3] == [("Team-Alpha", "Team-Beta")] * 3
    assert sched[3:] == [("Team-Beta", "Team-Alpha")] * 3


def test_resolve_teams_mirror_and_distinct() -> None:
    mirror = tr.resolve_teams(NetworkConfig(team_alpha_cop_url="ac", team_alpha_thief_url="at"))
    assert mirror["mirror"] is True and mirror["beta_cop"] == "ac"
    distinct = tr.resolve_teams(
        NetworkConfig(team_alpha_cop_url="ac", team_alpha_thief_url="at",
                      team_beta_cop_url="bc", team_beta_thief_url="bt")
    )
    assert distinct["mirror"] is False
    assert tr.sub_game_urls(distinct, "Team-Alpha") == ("ac", "bt")
    assert tr.sub_game_urls(distinct, "Team-Beta") == ("bc", "at")


def test_score_for_ledger() -> None:
    totals: dict = {}
    cop_win = tr.score_for(SubGameOutcome.COP_WINS, "Team-Alpha", "Team-Beta", totals)
    assert (cop_win["cop_points"], cop_win["thief_points"]) == (20, 5)
    thief_win = tr.score_for(SubGameOutcome.THIEF_WINS, "Team-Beta", "Team-Alpha", totals)
    assert (thief_win["cop_points"], thief_win["thief_points"]) == (5, 10)
    assert totals == {"Team-Alpha": 30, "Team-Beta": 10}


def test_run_series_six_games() -> None:
    controller = mock.Mock()
    controller.run_simulated_sub_game = mock.Mock(return_value=SubGameOutcome.COP_WINS)
    teams = tr.resolve_teams(NetworkConfig(team_alpha_cop_url="ac", team_alpha_thief_url="at"))
    sub_games, totals = tr.run_series(teams, controller=controller)
    assert len(sub_games) == 6
    assert controller.run_simulated_sub_game.call_count == 6
    assert sub_games[0]["sub_game"] == 1 and "cop_url" in sub_games[0]


def test_build_bonus_report_and_hash() -> None:
    teams = tr.resolve_teams(
        NetworkConfig(team_alpha_cop_url="ac", team_alpha_thief_url="at",
                      team_beta_cop_url="bc", team_beta_thief_url="bt")
    )
    sub_games = [{"sub_game": 1, "outcome": "cop_wins"}]
    report = tr.build_bonus_report(teams, sub_games, {"Team-Alpha": 20})
    assert report["report_type"] == "bonus_game"
    assert report["groups"] == {"group_1": "Team-Alpha", "group_2": "Team-Beta"}
    assert report["mcp_url_group_2_cop"] == "bc"
    assert len(report["agreement_sha256"]) == 64
    assert report["mutual_agreement"] is True
    assert tr.agreement_hash(sub_games) != tr.agreement_hash([{"sub_game": 2}])


def test_dispatch_report_burner_and_locked_production() -> None:
    gk = mock.Mock()
    gk.execute = mock.Mock(return_value={"id": "bonus-1"})
    reporter = GmailApiReporter(guard=SubmissionSafetyGuard(locked=True), gatekeeper=gk, service=None)
    out = tr.dispatch_report({"report_type": "bonus_game"}, production_drop=False, reporter=reporter)
    assert out["_delivery"] == {"id": "bonus-1"}
    with pytest.raises(SubmissionSafetyException):  # locked production blocks the examiner inbox
        tr.dispatch_report({"report_type": "bonus_game"}, production_drop=True, reporter=reporter)
