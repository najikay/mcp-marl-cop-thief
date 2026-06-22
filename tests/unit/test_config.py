"""Unit tests for config models and the ConfigManager loader."""

from __future__ import annotations

import json

import pytest

from cop_thief.config import ConfigManager
from cop_thief.config.models import GameConfig

_VALID = {
    "version": "1.0.0",
    "grid_size": [5, 5],
    "max_moves": 25,
    "num_games": 6,
    "max_barriers": 5,
    "scoring": {"cop_win": 20, "thief_win": 10, "cop_loss": 5, "thief_loss": 5},
}


def test_valid_config_loads():
    config = GameConfig.from_dict(_VALID)
    assert config.grid_size == (5, 5)
    assert config.scoring.cop_win == 20


def test_non_positive_grid_rejected():
    bad = {**_VALID, "grid_size": [0, 5]}
    with pytest.raises(ValueError):
        GameConfig.from_dict(bad)


def test_missing_scoring_key_rejected():
    bad = {**_VALID, "scoring": {"cop_win": 20}}
    with pytest.raises(ValueError):
        GameConfig.from_dict(bad)


def test_manager_reads_real_setup_file():
    config = ConfigManager().load()
    assert config.num_games == 6


def test_manager_missing_file(tmp_path):
    with pytest.raises(FileNotFoundError):
        ConfigManager(tmp_path / "nope.json").load()


def test_manager_malformed_json(tmp_path):
    path = tmp_path / "bad.json"
    path.write_text("{ not json", encoding="utf-8")
    with pytest.raises(ValueError):
        ConfigManager(path).load()


def test_manager_version_mismatch(tmp_path):
    path = tmp_path / "v.json"
    path.write_text(json.dumps({**_VALID, "version": "9.9.9"}), encoding="utf-8")
    with pytest.raises(ValueError):
        ConfigManager(path).load()
