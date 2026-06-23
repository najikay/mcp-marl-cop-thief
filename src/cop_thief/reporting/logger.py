"""Append-only JSON-Lines telemetry logger for dispute-proof game audit.

One JSON object per line (``data/game_audit.jsonl``) so standard CLI tools such
as ``jq`` can parse a live run turn-by-turn.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path


class GameTelemetryLogger:
    """Append immutable per-turn telemetry records as JSON Lines."""

    def __init__(self, audit_file: str | Path = "data/game_audit.jsonl") -> None:
        """Open (create) the append-only audit file's parent directory."""
        self._path = Path(audit_file)
        self._path.parent.mkdir(parents=True, exist_ok=True)

    def log_turn(
        self,
        turn_num: int,
        state_dict: dict,
        cop_prose: str,
        thief_prose: str,
        is_informed: bool,
        conway_active: bool,
    ) -> dict:
        """Append one turn record and return it.

        Args:
            turn_num: 1-based turn index.
            state_dict: Serializable board snapshot (positions, barriers, etc.).
            cop_prose: Raw natural-language transmission from the Cop.
            thief_prose: Raw natural-language transmission from the Thief.
            is_informed: Whether the Q-policy drove the turn (vs geometry).
            conway_active: Whether a Conway trap configuration was present.
        """
        record = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "turn": turn_num,
            "state": state_dict,
            "cop_prose": cop_prose,
            "thief_prose": thief_prose,
            "is_informed": bool(is_informed),
            "conway_active": bool(conway_active),
        }
        with self._path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")
        return record
