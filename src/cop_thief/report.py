"""Email the §9.2 bonus_game report from a CONFIRMED sub_games array.

Guarantees our own email goes out after the game even when the OPPONENT drove the
official series (treaty §8): we feed the agreed ``sub_games`` (the array whose digest
both sides confirmed EQUAL), build the exact §9.2 envelope, and send it. Run:
``uv run python -m cop_thief.report sub_games.json``  (the JSON array file they sent).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from cop_thief.config import get_config_manager
from cop_thief.reporting import GmailApiReporter
from cop_thief.reporting.bonus_report import build_bonus_report


def _ask(label: str, default: str = "") -> str:
    """Prompt for a value, returning the default when blank."""
    return input(f"{label}{f' [{default}]' if default else ''}: ").strip() or default


def main(argv: list[str] | None = None) -> None:
    """Build the bonus report from a confirmed sub_games file and email it."""
    argv = argv if argv is not None else sys.argv[1:]
    raw = Path(argv[0]).read_text(encoding="utf-8") if argv else _ask("sub_games JSON")
    sub_games = json.loads(raw)
    recipient = get_config_manager().setup.reporting.burner_email
    g1 = _ask("group_1 (Cop in sub-games 1-3)", "NajAmjad")
    g2 = _ask("group_2 (Cop in 4-6)", "Opponent")
    report = build_bonus_report(
        group_1=g1, group_2=g2,
        github=(_ask("github group_1"), _ask("github group_2")),
        mcp_urls={"g1_cop": _ask("g1 cop url"), "g1_thief": _ask("g1 thief url"),
                  "g2_cop": _ask("g2 cop url"), "g2_thief": _ask("g2 thief url")},
        students=([s for s in _ask("students group_1 (comma-sep)").split(",") if s],
                  [s for s in _ask("students group_2 (comma-sep)").split(",") if s]),
        sub_games=sub_games, mutual_agreement=True)
    print(f"agreement_sha256: {report['agreement_sha256']}  (must equal {g2}'s digest)")
    reporter = GmailApiReporter()
    reporter.bootstrap_oauth()
    reporter.dispatch_payload(report, _ask("send report to", recipient))
    print("Report emailed.")


if __name__ == "__main__":
    main()
