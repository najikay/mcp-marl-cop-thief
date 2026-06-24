"""Cross-host inter-group challenge: per-leg routing to a live opponent over MCP.

HOME leg (3 sub-games): we are Cop — our move is local, the Thief's move is fetched
from the opponent's Thief endpoint. AWAY leg (3 sub-games): we are Thief — our move
is local, the Cop's move is fetched from the opponent's Cop endpoint. Thief-first is
preserved. The report hashes the canonical ``sub_games`` (treaty §D); mutual_agreement
stays ``None`` (pending) until the opponent's report is compared.
"""

from __future__ import annotations

from cop_thief.domain.constants import AgentRole
from cop_thief.orchestrator.reconcile import canonical_hash
from cop_thief.orchestrator.series import SeriesRunner
from cop_thief.sdk.warfare import RetaliationLadder, is_hostile
from cop_thief.servers.tools.strategy_resolver import StrategyResolver

_TZ = "Asia/Jerusalem"


class ChallengeRunner:
    """Play 6 sub-games against a live opponent (our role local, their role remote)."""

    def __init__(self, our_group, opp_group, their_cop, their_thief,
                 our_resolver=None, observer=None, announce=None, turn_delay=0.0):
        """Wire group names, the opponent's remote move clients, our resolver and hooks."""
        self._our_group, self._opp_group = our_group, opp_group
        self._their_cop, self._their_thief = their_cop, their_thief
        self._our = our_resolver or StrategyResolver().resolve
        self._observer, self._announce, self._delay = observer, announce, turn_delay
        self._ladder = RetaliationLadder()

    def _say(self, msg: str) -> None:
        if self._announce is not None:
            self._announce(msg)

    def _retaliating(self, ours, theirs):
        """Wrap providers: flag the opponent's injections, escalate OUR counter-payload.

        The counter is *appended* to our move prose (our [INTENT] move stays at the front and
        intact), so it never alters our engine move — only a documented cheater draws fire.
        """
        def opponent(observation):
            prose = theirs(observation)
            self._ladder.register(is_hostile(prose))
            return prose

        def mine(observation):
            prose = ours(observation)
            payload = self._ladder.counter_payload(AgentRole(observation["role"]))
            return f"{prose} {payload}" if payload else prose

        return mine, opponent

    def run(self) -> dict:
        """Run both legs cross-host and return the scored, hashed bonus report."""
        legs = (("home", AgentRole.COP, self._their_thief),
                ("away", AgentRole.THIEF, self._their_cop))
        sub_games, totals = [], {"ours": 0, "opponent": 0}
        for venue, our_role, their in legs:
            mine, opponent = self._retaliating(self._our, their)
            cop_p, thief_p = (mine, opponent) if our_role is AgentRole.COP else (opponent, mine)
            runner = SeriesRunner(cop_p, thief_p, observer=self._observer,
                                  announce=self._announce, turn_delay=self._delay)
            self._say(f"{venue.upper()} LEG — we play {our_role.value.upper()} vs {self._opp_group}")
            for variant in range(3):
                self._say(f"Sub-game {len(sub_games) + 1}/6")
                outcome = runner.play_match(variant, index=len(sub_games))
                cop_pts, thief_pts = SeriesRunner._points(outcome)
                ours, opp = (cop_pts, thief_pts) if our_role is AgentRole.COP else (thief_pts, cop_pts)
                totals["ours"] += ours
                totals["opponent"] += opp
                sub_games.append({"match": len(sub_games) + 1, "venue": venue,
                                  "our_role": our_role.value, "outcome": outcome.value,
                                  "our_points": ours, "opponent_points": opp})
        return self._report(sub_games, totals)

    def _report(self, sub_games: list, totals: dict) -> dict:
        """Assemble the scored bonus report with the canonical sub_games hash."""
        diff = totals["ours"] - totals["opponent"]
        return {"report_type": "bonus_game",
                "groups": {"ours": self._our_group, "opponent": self._opp_group},
                "timezone": _TZ, "sub_games": sub_games, "totals": totals,
                "final_result": "ours" if diff > 0 else "opponent" if diff < 0 else "tie",
                "agreement_sha256": canonical_hash(sub_games), "mutual_agreement": None}
