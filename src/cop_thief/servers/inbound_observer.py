"""Passive end-of-game observer for when the OPPONENT drives the series.

Our MCP servers only ever see one ``request_move`` at a time, so this module-level
observer accumulates every observation (across the Cop and Thief tools), segments it
into sub-games (a new sub-game starts when the role flips or the turn counter resets),
infers each outcome, and — once the opponent goes idle — auto-emails the **same** ex06
§9.2 ``bonus_game`` report we send when WE initiate (``build_bonus_from_report``). This
guarantees our report goes out regardless of who ran the loop. Recipient defaults to
``reporting.burner_email`` (the test inbox now; switch to the examiner for the real run).
"""

from __future__ import annotations

import threading

from cop_thief.config import get_config_manager
from cop_thief.domain.constants import SubGameOutcome
from cop_thief.orchestrator.series import SeriesRunner
from cop_thief.reporting.bonus_report import build_bonus_from_report
from cop_thief.ui.node_state import STATE

_IDLE_SECONDS = 45.0


def _as_int(value) -> int:
    """Coerce an untrusted ``turn`` value to int (non-numeric → 0)."""
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


class InboundGameObserver:
    """Accumulate opponent-driven moves and auto-email the §9.2 report once idle."""

    def __init__(self, idle_seconds: float = _IDLE_SECONDS, emailer=None) -> None:
        """``emailer(report, recipient)`` is injectable for tests; else the Gmail reporter."""
        self._idle, self._emailer = idle_seconds, emailer
        self._lock = threading.Lock()
        self._timer: threading.Timer | None = None
        self._games: list[dict] = []
        self._cur: dict | None = None

    def record(self, role: str, observation: dict) -> None:
        """Note one observed move (called from each ``request_move``) and arm the idle flush."""
        turn = _as_int(observation.get("turn", 0))
        with self._lock:
            if self._cur is None or role != self._cur["role"] or turn < self._cur["max_turn"]:
                self._close_current()
                self._cur = {"role": role, "max_turn": turn}
            self._cur["max_turn"] = max(self._cur["max_turn"], turn)
            if self._timer is not None:
                self._timer.cancel()
            self._timer = threading.Timer(self._idle, self.flush)
            self._timer.daemon = True
            self._timer.start()

    def _close_current(self) -> None:
        """Score the in-progress sub-game from the turns observed and bank it."""
        if self._cur is None:
            return
        max_moves = get_config_manager().setup.game.max_moves
        survived = self._cur["max_turn"] >= max_moves - 2  # reached the wire → thief evaded
        outcome = SubGameOutcome.THIEF_WINS if survived else SubGameOutcome.COP_WINS
        cop_pts, thief_pts = SeriesRunner._points(outcome)
        we_cop = self._cur["role"] == "cop"
        ours, opp = (cop_pts, thief_pts) if we_cop else (thief_pts, cop_pts)
        self._games.append({"match": len(self._games) + 1, "venue": "home" if we_cop else "away",
                            "our_role": self._cur["role"], "outcome": outcome.value,
                            "our_points": ours, "opponent_points": opp})
        self._cur = None

    def flush(self) -> dict | None:
        """Finalize the observed game, build the §9.2 report, and email it (once)."""
        with self._lock:
            self._close_current()
            if not self._games:
                return None
            report = {"sub_games": self._games, "mutual_agreement": None}
            self._games = []
        bonus = build_bonus_from_report(report, STATE.cop_url, STATE.thief_url)
        self._send(bonus)
        return bonus

    def _send(self, bonus: dict) -> None:
        """Dispatch the report to the configured recipient (test inbox by default)."""
        recipient = get_config_manager().setup.reporting.burner_email
        if self._emailer is not None:
            self._emailer(bonus, recipient)
            return
        from google.auth.exceptions import GoogleAuthError

        from cop_thief.reporting import GmailApiReporter
        try:
            reporter = GmailApiReporter()
            reporter.bootstrap_oauth()
            reporter.dispatch_payload(bonus, recipient)
        except (OSError, RuntimeError, ValueError, GoogleAuthError):
            pass


OBSERVER = InboundGameObserver()
