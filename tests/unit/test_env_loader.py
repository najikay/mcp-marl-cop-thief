"""TDD unit tests for the zero-dependency .env autoloader."""

from __future__ import annotations

import os
from pathlib import Path

from cop_thief.config.env_loader import _apply_env, load_env_once


def test_apply_env_sets_absent_and_preserves_existing(tmp_path: Path) -> None:
    """New keys are populated; already-set env vars are never overwritten."""
    env = tmp_path / ".env"
    env.write_text(
        '# comment\nNEW_KEY_XYZ="from-file"\nEXISTING_KEY_XYZ=should-not-win\n'
        "export EXPORTED_KEY_XYZ='exp'\nMALFORMED_NO_EQUALS\n",
        encoding="utf-8",
    )
    os.environ["EXISTING_KEY_XYZ"] = "keep-me"
    try:
        _apply_env(env)
        assert os.environ["NEW_KEY_XYZ"] == "from-file"  # quotes stripped
        assert os.environ["EXISTING_KEY_XYZ"] == "keep-me"  # not clobbered
        assert os.environ["EXPORTED_KEY_XYZ"] == "exp"  # 'export ' prefix handled
        assert "MALFORMED_NO_EQUALS" not in os.environ  # skipped
    finally:
        for key in ("NEW_KEY_XYZ", "EXISTING_KEY_XYZ", "EXPORTED_KEY_XYZ"):
            os.environ.pop(key, None)


def test_load_env_once_missing_file_is_noop(tmp_path: Path) -> None:
    """A missing .env path is tolerated without error (idempotent guard)."""
    import cop_thief.config.env_loader as loader

    loader._LOADED = False
    load_env_once(env_path=tmp_path / "does-not-exist.env")
    assert loader._LOADED is True
    # Second call is a guarded no-op.
    load_env_once(env_path=tmp_path / "does-not-exist.env")
