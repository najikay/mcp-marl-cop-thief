"""Shared fixtures for the test suite."""

from __future__ import annotations

import pytest

from cop_thief.config.models import GameConfig


@pytest.fixture
def small_config() -> GameConfig:
    """A tiny, deterministic 2x2 config for fast end-to-end tests."""
    return GameConfig.from_dict(
        {
            "version": "1.0.0",
            "grid_size": [2, 2],
            "max_moves": 5,
            "num_games": 6,
            "max_barriers": 5,
            "random_start": True,
            "seed": 7,
            "scoring": {"cop_win": 20, "thief_win": 10, "cop_loss": 5, "thief_loss": 5},
        }
    )
