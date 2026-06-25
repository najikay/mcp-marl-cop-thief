"""TDD: the inbound observer auto-emails the §9.2 report when the OPPONENT drives."""

from __future__ import annotations

from cop_thief.servers.inbound_observer import InboundGameObserver


def _drive(obs: InboundGameObserver, role: str, turns) -> None:
    """Feed a sub-game's worth of observations for a role (turn counter ascending)."""
    for t in turns:
        obs.record(role, {"role": role, "grid": [5, 5], "cop": [0, 0], "thief": [4, 4],
                          "barriers": [], "barriers_left": 5, "turn": t})


def test_observer_emits_92_report_for_opponent_driven_game() -> None:
    """Six sub-games (3 Cop + 3 Thief) → one §9.2 bonus_game email to the configured inbox."""
    sent = []
    obs = InboundGameObserver(idle_seconds=999, emailer=lambda r, who: sent.append((r, who)))
    for _ in range(3):                       # we are Cop, captures early → cop_wins
        _drive(obs, "cop", [0, 2, 4])
    for _ in range(3):                       # we are Thief, survive to the wire → thief_wins
        _drive(obs, "thief", list(range(0, 25, 2)))
    report = obs.flush()
    assert report is not None and report["report_type"] == "bonus_game"
    assert len(report["sub_games"]) == 6
    assert sent and sent[0][0] is report     # emailed exactly what flush built
    g1 = report["groups"]["group_1"]
    assert report["totals_by_group"][g1] == 90  # 3×(Cop 20) + 3×(Thief 10)


def test_observer_idle_with_no_moves_sends_nothing() -> None:
    """A flush with nothing observed emails nothing (no stray reports)."""
    sent = []
    obs = InboundGameObserver(idle_seconds=999, emailer=lambda r, who: sent.append(r))
    assert obs.flush() is None and sent == []
