"""TDD unit tests for the JSON-Lines game telemetry logger."""

from __future__ import annotations

import json
from pathlib import Path

from cop_thief.reporting import GameTelemetryLogger


def test_log_turn_appends_jsonl(tmp_path: Path) -> None:
    """Each call appends exactly one parseable JSON object line."""
    audit = tmp_path / "game_audit.jsonl"
    logger = GameTelemetryLogger(audit_file=audit)

    record = logger.log_turn(
        1, {"cop": [0, 0], "thief": [4, 4]}, "I advance north-east", "I slip west", True, False
    )
    logger.log_turn(
        2, {"cop": [1, 1], "thief": [3, 3]}, "closing in", "dodging", False, True
    )

    lines = audit.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 2
    first = json.loads(lines[0])
    assert first["turn"] == 1
    assert first["state"] == {"cop": [0, 0], "thief": [4, 4]}
    assert first["cop_prose"] == "I advance north-east"
    assert first["is_informed"] is True
    assert first["conway_active"] is False
    assert "ts" in first
    assert record["turn"] == 1  # log_turn returns the written record

    second = json.loads(lines[1])
    assert second["is_informed"] is False
    assert second["conway_active"] is True
