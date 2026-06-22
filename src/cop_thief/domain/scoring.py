"""ScoringEngine — applies the immutable scoring matrix (PRD §3.4).

Point values are sourced from :class:`ScoringConfig` (config-driven) and never
mutated at runtime. A void (technical) sub-game scores zero for both sides.
"""

from __future__ import annotations

from ..config.models import ScoringConfig
from ..constants import SubGameOutcome


class ScoringEngine:
    """Map sub-game outcomes to ``(cop_points, thief_points)`` tuples."""

    def __init__(self, scoring: ScoringConfig) -> None:
        self._scoring = scoring

    def score(self, outcome: SubGameOutcome) -> tuple[int, int]:
        """Return ``(cop_points, thief_points)`` for a single sub-game outcome."""
        if outcome is SubGameOutcome.COP_WINS:
            return self._scoring.cop_win, self._scoring.thief_loss
        if outcome is SubGameOutcome.THIEF_WINS:
            return self._scoring.cop_loss, self._scoring.thief_win
        return 0, 0  # VOID_TECHNICAL scores nothing
