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


def build_internal_report(report: dict) -> dict:
    """Convert a played game into the exact ex06 §9.1 Internal Game JSON (for the auto-email).

    ``report`` carries the perspective-relative ``sub_games`` (``our_role``/``our_points``);
    totals are split by the role WE played (Cop sub-games vs Thief sub-games). Identity and our
    two MCP URLs come from config (no hardcoding). Body is JSON-only per ex06 §9.
    """
    cfg = get_config_manager()
    grp, net = cfg.setup.group, cfg.network
    sub = report["sub_games"]
    cop = sum(s["our_points"] for s in sub if s["our_role"] == "cop")
    thief = sum(s["our_points"] for s in sub if s["our_role"] == "thief")
    return {
        "group_name": grp.group_name, "students": list(grp.students),
        "github_repo": grp.github_repo, "cop_mcp_url": net.team_alpha_cop_url,
        "thief_mcp_url": net.team_alpha_thief_url, "timezone": _TZ,
        "sub_games": sub, "totals": {"cop": cop, "thief": thief},
    }
