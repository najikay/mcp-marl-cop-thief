"""Inter-group game runner: the full assignment pipeline (ONE game = 6 sub-games).

Per §4.1 a GAME is 6 sub-games: a HOME leg (our Cop hosts the guest Thief, 3
sub-games) and an AWAY leg (our Thief visits the opponent's Cop, 3 sub-games) —
thief-first, deterministic move language, live UI bus + audit log. Emails ONE
merged JSON report: per-sub-game venue/outcome/points, totals, result, SHA-256.
"""

from __future__ import annotations

import hashlib
import json
import time

from cop_thief.config import get_config_manager
from cop_thief.domain.constants import AgentRole, SubGameOutcome
from cop_thief.domain.grid import Grid
from cop_thief.domain.move_language import apply_prose
from cop_thief.domain.state import DecPomdpGameState
from cop_thief.sdk.services import MatchCoordinator
from cop_thief.sdk.warfare import is_hostile

_GRID = 5
_BURNER = "mcp.marl.telemetry@gmail.com"
_DIRECTIONS = (("home", AgentRole.COP), ("away", AgentRole.THIEF))


class SeriesRunner:
    """Run ONE game (6 sub-games over a HOME + AWAY leg) and email one merged report."""

    def __init__(self, cop_provider, thief_provider, observer=None, logger=None,
                 reporter=None, announce=None, recipient=_BURNER, max_moves=25, turn_delay=0.0):
        """Wire move providers, live observer, audit logger, reporter and UI banners."""
        self._cop = cop_provider
        self._thief = thief_provider
        self._observer = observer
        self._logger = logger
        self._reporter = reporter
        self._announce = announce
        self._recipient = recipient
        self._coord = MatchCoordinator(max_moves=max_moves)
        self._delay = turn_delay
        self._hostile = 0

    def _observation(self, state: DecPomdpGameState, role: AgentRole) -> dict:
        return {"role": role.value, "grid": list(state.grid.shape),
                "cop": list(state.cop_pos), "thief": list(state.thief_pos),
                "barriers": [list(b) for b in state.grid.barriers]}

    def _record(self, state: DecPomdpGameState, role: AgentRole, prose: str, hostile: bool) -> None:
        if self._observer is not None:
            self._observer(state, prose, False)
        if self._logger is not None:
            self._logger.log_turn(
                state.turn_counter,
                {"cop": list(state.cop_pos), "thief": list(state.thief_pos),
                 "barriers": [list(b) for b in state.grid.barriers]},
                prose if role is AgentRole.COP else "",
                prose if role is AgentRole.THIEF else "", False, False, hostile)

    def play_match(self) -> SubGameOutcome:
        """Play one thief-first sub-game by asking each provider for its move."""
        state = DecPomdpGameState(
            cop_pos=(0, 0), thief_pos=(_GRID - 1, _GRID - 1), grid=Grid(shape=(_GRID, _GRID)))
        for _ in range(self._coord.max_moves * 2):
            outcome = self._coord.evaluate_terminal_condition(state)
            if outcome is not None:
                return outcome
            role = state.turn_role
            provider = self._cop if role is AgentRole.COP else self._thief
            prose = provider(self._observation(state, role))
            self._hostile += int(hostile := is_hostile(prose))
            state = apply_prose(state, role, prose)
            self._record(state, role, prose, hostile)
            if self._delay:
                time.sleep(self._delay)
        return self._coord.evaluate_terminal_condition(state) or SubGameOutcome.THIEF_WINS

    @staticmethod
    def _points(outcome: SubGameOutcome) -> tuple[int, int]:
        sc = get_config_manager().setup.scoring
        if outcome in (SubGameOutcome.COP_WINS, SubGameOutcome.THIEF_TRAPPED):
            return sc.cop_win, sc.thief_loss
        return sc.cop_loss, sc.thief_win

    def run_series(self) -> dict:
        """Run both legs (6 sub-games), score them, email one merged report."""
        sub_games, totals = [], {"ours": 0, "opponent": 0}
        for venue, our_role in _DIRECTIONS:
            if self._announce is not None:
                self._announce(f"{venue.upper()} LEG — we play {our_role.value.upper()} (3 sub-games)")
            for _ in range(3):
                if self._announce is not None:
                    self._announce(f"Sub-game {len(sub_games) + 1}/6")
                outcome = self.play_match()
                cop_pts, thief_pts = self._points(outcome)
                ours, opp = (cop_pts, thief_pts) if our_role is AgentRole.COP else (thief_pts, cop_pts)
                totals["ours"] += ours
                totals["opponent"] += opp
                sub_games.append({"match": len(sub_games) + 1, "venue": venue,
                                  "our_role": our_role.value, "outcome": outcome.value,
                                  "our_points": ours, "opponent_points": opp})
        report = self._report(sub_games, totals)
        if self._reporter is not None:
            self._reporter.dispatch_payload(report, self._recipient)
        return report

    def _report(self, sub_games: list, totals: dict) -> dict:
        net = get_config_manager().network
        diff = totals["ours"] - totals["opponent"]
        canon = json.dumps(sub_games, sort_keys=True, separators=(",", ":"))
        return {
            "report_type": "game_report", "groups": {"ours": "Team-Alpha", "opponent": "Team-Beta"},
            "our_cop_url": net.team_alpha_cop_url, "our_thief_url": net.team_alpha_thief_url, "opponent_cop_url": net.team_beta_cop_url, "opponent_thief_url": net.team_beta_thief_url,
            "timezone": "Asia/Jerusalem", "sub_games": sub_games, "totals": totals, "hostile_transmissions": self._hostile,
            "final_result": "ours" if diff > 0 else "opponent" if diff < 0 else "tie",
            "agreement_sha256": hashlib.sha256(canon.encode("utf-8")).hexdigest(),
        }
