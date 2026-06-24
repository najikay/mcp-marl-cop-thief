"""Mutual-agreement reconciliation: if the two reports disagree, both lose.

Per the treaty (§D.5) both groups independently hash the ``sub_games`` array; a
match sets ``mutual_agreement = true`` and keeps the scored totals, while **any**
mismatch forces ``mutual_agreement = false`` and a 0/0 scoreline ("both lose").
This is the structural enforcement of "if we disagree, we both lose".
"""

from __future__ import annotations

import hashlib
import json

_TOTALS_KEYS = ("totals", "totals_by_group")


def canonical_hash(sub_games: list) -> str:
    """SHA-256 over the canonical ``sub_games`` array (treaty §D pipeline)."""
    canonical = json.dumps(sub_games, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _digest(report: dict) -> str:
    """Return the report's stated agreement hash, or compute it from ``sub_games``."""
    return report.get("agreement_sha256") or canonical_hash(report.get("sub_games", []))


def reconcile_agreement(our_report: dict, partner_report: dict) -> dict:
    """Compare both agreement hashes; on mismatch zero both totals (both lose).

    Returns an adjudicated copy of ``our_report`` carrying ``mutual_agreement``,
    the ``partner_agreement_sha256`` seen, and — on mismatch — zeroed totals and
    a ``final_result`` of ``"both_lose"``.
    """
    ours, theirs = _digest(our_report), _digest(partner_report)
    agreed = bool(ours) and ours == theirs
    adjudicated = {
        **our_report,
        "agreement_sha256": ours,
        "partner_agreement_sha256": theirs,
        "mutual_agreement": agreed,
    }
    if agreed:
        return adjudicated
    for key in _TOTALS_KEYS:
        if key in adjudicated:
            adjudicated[key] = dict.fromkeys(our_report[key], 0)
    adjudicated["final_result"] = "both_lose"
    return adjudicated
