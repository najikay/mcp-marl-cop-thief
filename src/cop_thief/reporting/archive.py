"""Immutable per-game dispute archive — tamper-evident evidence to prove cheating.

Collects every transmission of one inter-group game (both sides) with its board snapshot
and hostility verdict, then seals a single JSON bundle under ``data/archive/`` carrying a
SHA-256 over the whole record. Editing any byte afterwards breaks the seal, so the bundle is
verifiable evidence for lecturer adjudication if the opponent later disputes the result.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


def _sha(payload) -> str:
    """Canonical SHA-256 (sorted keys, no whitespace) over a JSON-serializable payload."""
    canon = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canon.encode("utf-8")).hexdigest()


def _utc() -> str:
    return datetime.now(timezone.utc).isoformat()


class DisputeArchive:
    """Collect one game's transmissions and seal them into an immutable evidence bundle."""

    def __init__(self, our_group: str, opp_group: str, archive_dir: str | Path = "data/archive") -> None:
        """Bind the two group names and the output directory; start an empty transmission log."""
        self._our, self._opp = our_group, opp_group
        self._dir = Path(archive_dir)
        self._turns: list[dict] = []

    def record(self, observation: dict, prose: str, hostile: bool) -> None:
        """Append one transmission (board snapshot + role + prose + hostility) as evidence."""
        board = {"turn": observation.get("turn"), "cop": observation.get("cop"),
                 "thief": observation.get("thief"), "barriers": observation.get("barriers", [])}
        self._turns.append({"ts": _utc(), "role": observation.get("role"), "prose": prose,
                            "hostile": bool(hostile), "board": board, "board_sha256": _sha(board)})

    def seal(self, report: dict) -> dict:
        """Write the sealed, tamper-evident bundle to disk and return it."""
        hostile = [t for t in self._turns if t["hostile"]]
        bundle = {
            "report_type": "dispute_archive",
            "groups": {"ours": self._our, "opponent": self._opp},
            "sealed_utc": _utc(),
            "turns": self._turns,
            "evidence": {
                "transmissions": len(self._turns),
                "hostile_count": len(hostile),
                "hostile_transmissions": [{"role": t["role"], "prose": t["prose"]} for t in hostile],
                "agreement_sha256": report.get("agreement_sha256"),
                "final_result": report.get("final_result"),
            },
            "report": report,
        }
        bundle["bundle_sha256"] = _sha(bundle)  # seals everything above (excludes itself)
        self._dir.mkdir(parents=True, exist_ok=True)
        safe = "".join(c if (c.isalnum() or c in "-_") else "-" for c in self._opp) or "opponent"
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        (self._dir / f"game_{stamp}_{safe}.json").write_text(
            json.dumps(bundle, indent=2, ensure_ascii=False), encoding="utf-8")
        return bundle
