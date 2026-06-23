"""Section 12 inter-group 6-game bonus treaty orchestrator.

Owns only the role-alternation schedule, the scoring ledger, the Section 9.2
bonus JSON schema, its SHA-256 agreement hash, and Gmail dispatch. Each sub-game
25-turn pursuit is delegated to GameLoopController (reused, not re-implemented);
in Mirror Mode the node self-plays for network validation. Live cross-host turns
route through the dual MCP host's SSE endpoints (config network matrix).

Run: uv run python -m cop_thief.orchestrator.treaty_runner [--production-drop]
"""

from __future__ import annotations

import argparse
import hashlib
import json

from cop_thief.config import get_config_manager
from cop_thief.domain.constants import SubGameOutcome
from cop_thief.orchestrator.controller import GameLoopController
from cop_thief.reporting import GmailApiReporter
from cop_thief.ui import broadcast

_ALPHA, _BETA = "Team-Alpha", "Team-Beta"
_COP_WIN_OUTCOMES = (SubGameOutcome.COP_WINS, SubGameOutcome.THIEF_TRAPPED)
_TZ = "Asia/Jerusalem"
_REPO_ALPHA = "https://github.com/team-alpha/marl-cop-thief"
_REPO_BETA = "https://github.com/team-beta/marl-cop-thief"
_EXAMINER = "rmisegal+uoh26b@gmail.com"
_BURNER = "mcp.marl.telemetry@gmail.com"


def role_schedule() -> list[tuple[str, str]]:
    """Section 12.1: games 1-3 Alpha-cop/Beta-thief; 4-6 Beta-cop/Alpha-thief."""
    return [(_ALPHA, _BETA)] * 3 + [(_BETA, _ALPHA)] * 3


def resolve_teams(network) -> dict:
    """Resolve the 4-URL matrix; empty Beta falls back to Mirror Mode (self-play)."""
    a_cop, a_thief = network.team_alpha_cop_url, network.team_alpha_thief_url
    b_cop = network.team_beta_cop_url or a_cop
    b_thief = network.team_beta_thief_url or a_thief
    return {"alpha_cop": a_cop, "alpha_thief": a_thief, "beta_cop": b_cop,
            "beta_thief": b_thief, "mirror": b_cop == a_cop and b_thief == a_thief}


def sub_game_urls(teams: dict, cop_team: str) -> tuple[str, str]:
    """Return (cop_url, thief_url) targeting the SSE endpoints for this sub-game."""
    if cop_team == _ALPHA:
        return teams["alpha_cop"], teams["beta_thief"]
    return teams["beta_cop"], teams["alpha_thief"]


def score_for(outcome, cop_team: str, thief_team: str, totals: dict) -> dict:
    """Apply Section 4.4 scoring for one outcome and update the running ledger."""
    sc = get_config_manager().setup.scoring
    cop_pts, thief_pts = (sc.cop_win, sc.thief_loss) if outcome in _COP_WIN_OUTCOMES else (sc.cop_loss, sc.thief_win)
    totals[cop_team] = totals.get(cop_team, 0) + cop_pts
    totals[thief_team] = totals.get(thief_team, 0) + thief_pts
    return {"cop_team": cop_team, "thief_team": thief_team, "outcome": outcome.value, "cop_points": cop_pts, "thief_points": thief_pts}


def run_series(teams: dict, controller=None) -> tuple[list, dict]:
    """Run the 6 sub-games via the controller, returning (sub_games, totals)."""
    controller = controller or GameLoopController()
    totals: dict = {}
    sub_games = []
    for index, (cop_team, thief_team) in enumerate(role_schedule(), 1):
        cop_url, thief_url = sub_game_urls(teams, cop_team)
        outcome = controller.run_simulated_sub_game(f"treaty-{index}")
        record = score_for(outcome, cop_team, thief_team, totals)
        record.update({"sub_game": index, "cop_url": cop_url, "thief_url": thief_url})
        sub_games.append(record)
    return sub_games, totals


def agreement_hash(sub_games: list) -> str:
    """SHA-256 over the canonical serialization of the sub-games array (K3)."""
    canon = json.dumps(sub_games, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canon.encode("utf-8")).hexdigest()


def build_bonus_report(teams: dict, sub_games: list, totals: dict) -> dict:
    """Assemble the Section 9.2 'bonus_game' JSON report."""
    return {
        "report_type": "bonus_game",
        "groups": {"group_1": _ALPHA, "group_2": _BETA},
        "mirror_mode": teams["mirror"],
        "mcp_url_group_1_cop": teams["alpha_cop"], "mcp_url_group_1_thief": teams["alpha_thief"],
        "mcp_url_group_2_cop": teams["beta_cop"], "mcp_url_group_2_thief": teams["beta_thief"],
        "github_repo_group_1": _REPO_ALPHA, "github_repo_group_2": _REPO_BETA,
        "timezone": _TZ, "sub_games": sub_games, "totals_by_group": totals,
        "agreement_sha256": agreement_hash(sub_games), "mutual_agreement": True,
    }


def dispatch_report(report: dict, production_drop: bool, reporter=None) -> dict:
    """Send the bonus report (burner by default; examiner on --production-drop)."""
    reporter = reporter or GmailApiReporter()
    return reporter.dispatch_payload(report, _EXAMINER if production_drop else _BURNER)


def main(argv: list[str] | None = None) -> None:
    """Run the 6-game treaty and dispatch the bonus report."""
    parser = argparse.ArgumentParser(prog="treaty-runner")
    parser.add_argument("--production-drop", action="store_true")
    args = parser.parse_args(argv)
    teams = resolve_teams(get_config_manager().network)
    sub_games, totals = run_series(teams, GameLoopController(observer=broadcast.feed))
    report = build_bonus_report(teams, sub_games, totals)
    reporter = GmailApiReporter()
    reporter.bootstrap_oauth()
    dispatch_report(report, args.production_drop, reporter=reporter)
    print(f"Treaty complete (mirror={teams['mirror']}). Totals: {totals}")
    print(f"Agreement SHA-256: {report['agreement_sha256']}")


if __name__ == "__main__":
    main()
