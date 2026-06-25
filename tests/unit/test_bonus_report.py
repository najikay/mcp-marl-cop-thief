"""TDD: the exact ex06 §9.2 bonus_game schema + treaty-§D canonical sub_games + agreement."""

from __future__ import annotations

from cop_thief.orchestrator.reconcile import canonical_hash, reconcile_agreement
from cop_thief.reporting.bonus_report import (
    build_bonus_report,
    build_internal_report,
    canonical_sub_games,
    totals_by_group,
)

_URLS = {"our_cop": "https://a-cop/mcp/", "our_thief": "https://a-thief/mcp/",
         "opp_cop": "https://b-cop/mcp/", "opp_thief": "https://b-thief/mcp/"}
_RESULTS = [
    {"match": 1, "venue": "home", "our_role": "cop", "outcome": "cop_wins", "our_points": 20, "opponent_points": 5},
    {"match": 4, "venue": "away", "our_role": "thief", "outcome": "thief_wins", "our_points": 10, "opponent_points": 5},
]


def test_canonical_sub_games_map_roles_points_and_urls() -> None:
    """Home → we are Cop; Away → we are Thief; teams/points/urls are assigned accordingly."""
    canon = canonical_sub_games("NajAmjad", "Beta", _URLS, _RESULTS)
    home, away = canon
    assert home["cop_team"] == "NajAmjad" and home["thief_team"] == "Beta"
    assert home["cop_points"] == 20 and home["cop_url"] == "https://a-cop/mcp/"
    assert away["cop_team"] == "Beta" and away["thief_team"] == "NajAmjad"
    assert away["thief_points"] == 10 and away["thief_url"] == "https://a-thief/mcp/"
    assert set(home) == {"sub_game", "cop_team", "thief_team", "outcome",
                         "cop_points", "thief_points", "cop_url", "thief_url"}


def test_build_bonus_report_has_exact_92_schema() -> None:
    """The envelope carries every §9.2 key and a treaty-§D hash over the sub_games."""
    canon = canonical_sub_games("NajAmjad", "Beta", _URLS, _RESULTS)
    report = build_bonus_report(
        group_1="NajAmjad", group_2="Beta",
        github=("https://github.com/naj/x", "https://github.com/beta/y"),
        mcp_urls={"g1_cop": "u1", "g1_thief": "u2", "g2_cop": "u3", "g2_thief": "u4"},
        students=(["Naji", "Amjad"], ["B1"]), sub_games=canon, mutual_agreement=True)
    for key in ("report_type", "groups", "github_repo_group_1", "github_repo_group_2",
                "mcp_url_group_1_cop", "mcp_url_group_2_thief", "students_group_1",
                "totals_by_group", "agreement_sha256", "mutual_agreement", "bonus_claim"):
        assert key in report
    assert report["report_type"] == "bonus_game"
    assert report["agreement_sha256"] == canonical_hash(canon)
    assert report["totals_by_group"] == {"NajAmjad": 30, "Beta": 10}
    assert report["bonus_claim"] == {"NajAmjad": 10, "Beta": 10}  # §9.2: dict of group -> claimed pts


def test_internal_report_has_exact_91_schema() -> None:
    """build_internal_report emits the §9.1 Internal Game JSON with role-split totals."""
    rich = {"sub_games": [
        {"match": 1, "our_role": "cop", "our_points": 20},
        {"match": 2, "our_role": "cop", "our_points": 5},
        {"match": 3, "our_role": "thief", "our_points": 10}]}
    rep = build_internal_report(rich)
    assert set(rep) == {"group_name", "students", "github_repo", "cop_mcp_url",
                        "thief_mcp_url", "timezone", "sub_games", "totals"}
    assert rep["totals"] == {"cop": 25, "thief": 10}
    assert rep["group_name"]  # config-driven identity, non-empty


def test_both_groups_hash_identically_so_reports_agree() -> None:
    """Both sides build over the same canonical sub_games → mutual agreement holds (#444)."""
    canon = canonical_sub_games("NajAmjad", "Beta", _URLS, _RESULTS)
    ours = build_bonus_report(group_1="NajAmjad", group_2="Beta", github=("g1", "g2"),
                              mcp_urls={"g1_cop": "u1", "g1_thief": "u2", "g2_cop": "u3", "g2_thief": "u4"},
                              students=(["Naji"], ["B"]), sub_games=canon)
    theirs = dict(ours)  # the opponent independently produces the byte-identical sub_games
    verdict = reconcile_agreement(ours, theirs)
    assert verdict["mutual_agreement"] is True


def test_totals_by_group_sums_both_roles() -> None:
    """Each group's total sums its Cop points and its Thief points across sub_games."""
    canon = canonical_sub_games("NajAmjad", "Beta", _URLS, _RESULTS)
    assert totals_by_group(canon, "NajAmjad", "Beta") == {"NajAmjad": 30, "Beta": 10}
