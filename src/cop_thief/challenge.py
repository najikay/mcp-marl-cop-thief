"""Interactive cross-host challenge: paste the opponent's URLs and play a real game.

Run: ``uv run python -m cop_thief.challenge`` — prompts for our/their group names, the
opponent's COP & THIEF MCP URLs (the values they shared, e.g. ``…/mcp/`` or ``…/sse``),
their tokens and the report email. It first does a connectivity **preflight** against
their ``request_move`` tool, then plays the 6-sub-game game (our moves local, the
opponent's fetched over MCP) and emails the JSON report.
"""

from __future__ import annotations

import os

from cop_thief.config import get_config_manager
from cop_thief.infra.network.move_client import RemoteMoveClient
from cop_thief.orchestrator.challenge_runner import ChallengeRunner
from cop_thief.reporting import GmailApiReporter

_PROBE = {"grid": [5, 5], "cop": [0, 0], "thief": [4, 4], "barriers": [], "barriers_left": 5, "variant": 0}


def _ask(label: str, default: str = "") -> str:
    """Prompt for a value, returning the default when the input is blank."""
    suffix = f" [{default}]" if default else ""
    return input(f"{label}{suffix}: ").strip() or default


def _preflight(client: RemoteMoveClient, role: str) -> None:
    """Call the opponent's request_move once to confirm cross-host interop."""
    print(f"Preflight -> opponent {role}.request_move ...")
    print(f"   reply: {client({**_PROBE, 'role': role})}")


def _show(state, prose: str, informed: bool) -> None:
    """Print one resolved turn to the console (the acting agent + its prose)."""
    actor = "thief" if state.turn_role.value == "cop" else "cop"
    print(f"   T{state.turn_counter:>2} {actor:<5} {prose}")


def main() -> None:
    """Prompt for opponent details, preflight, play the game and email the report."""
    our = _ask("Our group name", "NajAmjad")
    opp = _ask("Opponent group name", "Team-Beta")
    cop_url = _ask("Opponent COP MCP URL")
    thief_url = _ask("Opponent THIEF MCP URL")
    results_inbox = get_config_manager().setup.reporting.burner_email
    email = _ask("Send report to email", results_inbox)
    cop_tok = _ask("Opponent COP token", os.environ.get("BETA_COP_TOKEN", ""))
    thief_tok = _ask("Opponent THIEF token", os.environ.get("BETA_THIEF_TOKEN", ""))
    their_cop = RemoteMoveClient(cop_url, cop_tok)
    their_thief = RemoteMoveClient(thief_url, thief_tok)
    _preflight(their_cop, "cop")
    _preflight(their_thief, "thief")
    runner = ChallengeRunner(our, opp, their_cop, their_thief, observer=_show, announce=print)
    report = runner.run()
    report.update({"opponent_cop_url": cop_url, "opponent_thief_url": thief_url, "opponent_email": email})
    print(f"Totals: {report['totals']} | our agreement hash: {report['agreement_sha256']}")
    reporter = GmailApiReporter()
    reporter.bootstrap_oauth()
    reporter.dispatch_payload(report, email)
    print(f"Report emailed to {email}. Compare hashes with {opp} for mutual agreement.")


if __name__ == "__main__":
    main()
