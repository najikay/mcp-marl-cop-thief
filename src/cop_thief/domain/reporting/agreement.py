"""Mutual-agreement reconciliation and bonus scoring (PRD §3.5).

The non-negotiable bonus gate K3: both groups must independently report the
**same** result. :class:`AgreementReconciler` compares the result-bearing parts
of two reports; on mismatch the series is cancelled (0 for both). Scoring per
series: winner 10, loser 7, exact tie 5 each; the final bonus is the average
over all valid series.
"""

from __future__ import annotations

import json


def compute_bonus_claim(totals_by_group: dict[str, int]) -> dict[str, int]:
    """Map per-group totals to bonus points: 10 / 7, or 5 each on a tie."""
    names = list(totals_by_group)
    if len(names) != 2:
        raise ValueError("a bonus series must have exactly two groups")
    first, second = names
    if totals_by_group[first] == totals_by_group[second]:
        return {first: 5, second: 5}
    winner = first if totals_by_group[first] > totals_by_group[second] else second
    return {name: (10 if name == winner else 7) for name in names}


def average_bonus(points_per_series: list[float]) -> float:
    """Final bonus = mean of a group's points across all valid series."""
    if not points_per_series:
        return 0.0
    return sum(points_per_series) / len(points_per_series)


class AgreementReconciler:
    """Decide whether two groups' reports describe the identical outcome."""

    def reconcile(self, report_a: dict, report_b: dict) -> bool:
        """True if both reports agree on totals and per-sub-game outcomes (K3)."""
        return self._fingerprint(report_a) == self._fingerprint(report_b)

    @staticmethod
    def _fingerprint(report: dict) -> str:
        """Canonical signature of the result-bearing fields only."""
        core = {
            "totals_by_group": report.get("totals_by_group"),
            "sub_games": report.get("sub_games"),
        }
        return json.dumps(core, sort_keys=True, ensure_ascii=False)
