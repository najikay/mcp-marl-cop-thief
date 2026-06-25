"""Exact ex06 §9.2 ``bonus_game`` report — the inter-group submission envelope.

Converts a played game (our per-sub-game results) into the **treaty §D canonical** ``sub_games``
(cop_team / thief_team / points / urls) so BOTH groups hash an identical array, then wraps it in
the §9.2 schema: groups, both github repos, the four ``mcp_url_*``, students, ``totals_by_group``,
``agreement_sha256``, ``mutual_agreement`` and ``bonus_claim``.
"""

from __future__ import annotations

from cop_thief.config import get_config_manager
from cop_thief.orchestrator.reconcile import canonical_hash

_TZ = "Asia/Jerusalem"


def canonical_sub_games(our_group: str, opp_group: str, urls: dict, results: list) -> list[dict]:
    """Map our per-sub-game results to the treaty §D canonical entries (identical both sides).

    ``results`` are ``ChallengeRunner`` rows (``venue`` home = we are Cop, away = we are Thief);
    ``urls`` carries ``our_cop / our_thief / opp_cop / opp_thief``.
    """
    canonical = []
    for row in results:
        we_cop = row["venue"] == "home"
        cop_team, thief_team = (our_group, opp_group) if we_cop else (opp_group, our_group)
        cop_url, thief_url = ((urls["our_cop"], urls["opp_thief"]) if we_cop
                              else (urls["opp_cop"], urls["our_thief"]))
        cop_pts, thief_pts = ((row["our_points"], row["opponent_points"]) if we_cop
                              else (row["opponent_points"], row["our_points"]))
        canonical.append({
            "sub_game": row["match"], "cop_team": cop_team, "thief_team": thief_team,
            "outcome": row["outcome"], "cop_points": cop_pts, "thief_points": thief_pts,
            "cop_url": cop_url, "thief_url": thief_url,
        })
    return canonical


def totals_by_group(sub_games: list, group_1: str, group_2: str) -> dict:
    """Sum each group's Cop+Thief points across the canonical sub_games."""
    totals = {group_1: 0, group_2: 0}
    for game in sub_games:
        totals[game["cop_team"]] += game["cop_points"]
        totals[game["thief_team"]] += game["thief_points"]
    return totals


def build_bonus_report(*, group_1: str, group_2: str, github: tuple, mcp_urls: dict, students: tuple,
                       sub_games: list, mutual_agreement=None, bonus_claim=None) -> dict:
    """Assemble the exact §9.2 ``bonus_game`` envelope with a treaty-§D agreement hash."""
    claim = bonus_claim if bonus_claim is not None else {group_1: 10, group_2: 10}
    return {
        "report_type": "bonus_game",
        "groups": {"group_1": group_1, "group_2": group_2},
        "github_repo_group_1": github[0], "github_repo_group_2": github[1],
        "mcp_url_group_1_cop": mcp_urls["g1_cop"], "mcp_url_group_1_thief": mcp_urls["g1_thief"],
        "mcp_url_group_2_cop": mcp_urls["g2_cop"], "mcp_url_group_2_thief": mcp_urls["g2_thief"],
        "students_group_1": list(students[0]), "students_group_2": list(students[1]),
        "timezone": _TZ, "sub_games": sub_games,
        "totals_by_group": totals_by_group(sub_games, group_1, group_2),
        "agreement_sha256": canonical_hash(sub_games),
        "mutual_agreement": mutual_agreement, "bonus_claim": claim,
    }


def build_bonus_from_report(report: dict, our_cop_url: str = "", our_thief_url: str = "") -> dict:
    """Convert a played inter-group game into the exact ex06 §9.2 ``bonus_game`` envelope.

    This is what the Cop auto-emails at game end (§9). We are ``group_1``, the opponent
    ``group_2`` (both from config). Our two MCP URLs are taken **live** (the dynamic tunnel
    URLs of this session) with a config fallback — we hold no permanent URL; the opponent's
    come from config. The perspective-relative ``sub_games`` (``our_role``/``our_points``) are
    mapped to the treaty-§D canonical array so both groups hash identically. ``mutual_agreement``
    carries through from the run (``None`` until the two digests are reconciled).
    """
    cfg = get_config_manager()
    grp, opp, net = cfg.setup.group, cfg.setup.opponent, cfg.network
    urls = {"our_cop": our_cop_url or net.team_alpha_cop_url,
            "our_thief": our_thief_url or net.team_alpha_thief_url,
            "opp_cop": net.team_beta_cop_url, "opp_thief": net.team_beta_thief_url}
    canon = canonical_sub_games(grp.group_name, opp.group_name, urls, report["sub_games"])
    return build_bonus_report(
        group_1=grp.group_name, group_2=opp.group_name,
        github=(grp.github_repo, opp.github_repo),
        mcp_urls={"g1_cop": urls["our_cop"], "g1_thief": urls["our_thief"],
                  "g2_cop": urls["opp_cop"], "g2_thief": urls["opp_thief"]},
        students=(grp.students, opp.students),
        sub_games=canon, mutual_agreement=report.get("mutual_agreement"))
