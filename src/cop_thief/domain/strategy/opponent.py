"""Online opponent-rationality model that drives the planner's pessimism knob.

We can't *train* a value function in a few matches, but we **can** detect whether the
opponent is playing rationally and adapt. Each observed opponent move is judged by a
cheap geometric proxy (did the Thief flee / did the Cop close in?); the running
rational-rate becomes the planner's ``pessimism``: an optimal opponent → pessimism→1
(pure minimax, unexploitable), a sloppy/random one → pessimism↓ (expectimax exploits).
"""

from __future__ import annotations


def _chebyshev(a: tuple, b: tuple) -> int:
    return max(abs(a[0] - b[0]), abs(a[1] - b[1]))


def opponent_was_rational(we_are: str, prev: dict, now: dict) -> bool:
    """Judge the opponent's last move from two consecutive of OUR observations.

    Opponent = the role we are not. A rational Thief increases distance from the Cop's
    current cell; a rational Cop decreases distance to the Thief's current cell.
    """
    now_cop, now_thief = tuple(now["cop"]), tuple(now["thief"])
    if we_are == "cop":  # opponent is the Thief — did it flee the Cop's current cell?
        return _chebyshev(now_thief, now_cop) >= _chebyshev(tuple(prev["thief"]), now_cop)
    return _chebyshev(now_cop, now_thief) <= _chebyshev(tuple(prev["cop"]), now_thief)


class OpponentModel:
    """Track the opponent's demonstrated rationality and expose it as a pessimism in [0,1]."""

    def __init__(self) -> None:
        """Start with no evidence (assume an optimal opponent → maximal pessimism)."""
        self._rational = 0
        self._total = 0

    def observe(self, rational: bool) -> None:
        """Record one judged opponent move."""
        self._total += 1
        self._rational += int(bool(rational))

    def pessimism(self) -> float:
        """Return the rational-rate (1.0 with no data — stay safe until proven exploitable)."""
        return 1.0 if self._total == 0 else self._rational / self._total
