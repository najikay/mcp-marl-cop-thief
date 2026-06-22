"""TDD unit tests for the configuration subsystem.

Covers three mandated scenarios:
1. Happy-path loading of the real shipped config files.
2. A version-mismatched ``setup.json`` raising ``ConfigurationVersionError``.
3. A ``setup.json`` missing a required key raising Pydantic ``ValidationError``.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from cop_thief.config import ConfigManager, ConfigurationVersionError

PROJECT_ROOT = Path(__file__).resolve().parents[2]
REAL_CONFIG_DIR = PROJECT_ROOT / "config"


def _valid_setup() -> dict:
    """Return a minimal-but-complete valid ``setup.json`` mapping."""
    return {
        "version": "1.00",
        "game": {"grid_size": [5, 5], "max_moves": 25, "num_games": 6, "max_barriers": 5},
        "scoring": {"cop_win": 20, "thief_win": 10, "cop_loss": 5, "thief_loss": 5},
        "servers": {
            "cop": {"mode": "cloud", "url": "https://c", "auth_env_var": "COP_MCP_TOKEN"},
            "thief": {"mode": "cloud", "url": "https://t", "auth_env_var": "THIEF_MCP_TOKEN"},
        },
        "llm_routing": {
            "primary": {
                "provider": "DEEPSEEK", "base_url": "https://api.deepseek.com",
                "model": "deepseek-chat", "api_key_env_var": "DEEPSEEK_API_KEY",
            },
            "fallback": {
                "provider": "ANTHROPIC", "base_url": "https://api.anthropic.com",
                "model": "claude-3-5-sonnet-20241022", "api_key_env_var": "ANTHROPIC_API_KEY",
            },
        },
        "rl": {
            "rewards": {
                "r_capture": 20, "r_evasion": 10, "r_caught": -10,
                "r_step": -1, "r_invalid": -5,
            }
        },
        "token_budget": {
            "version": "1.00",
            "rates": {"input_per_million_usd": 0.15, "output_per_million_usd": 0.60},
            "ceiling_usd": 5.0,
        },
    }


def _valid_rate_limits() -> dict:
    """Return a minimal valid ``rate_limits.json`` mapping."""
    return {
        "version": "1.00",
        "rate_limits": {
            "services": {
                "default": {
                    "requests_per_minute": 30, "concurrent_max": 5,
                    "retry_after_seconds": 30, "max_retries": 3, "queue_max_depth": 100,
                }
            }
        },
    }


def _valid_logging() -> dict:
    """Return a minimal valid ``logging_config.json`` mapping."""
    return {"version": 1, "handlers": {}, "root": {"level": "WARNING"}}


def _write_config_dir(target: Path, setup: dict | None = None) -> Path:
    """Materialise a full config directory in ``target`` and return it."""
    (target / "setup.json").write_text(json.dumps(setup or _valid_setup()), encoding="utf-8")
    (target / "rate_limits.json").write_text(json.dumps(_valid_rate_limits()), encoding="utf-8")
    (target / "logging_config.json").write_text(json.dumps(_valid_logging()), encoding="utf-8")
    return target


def test_happy_path_loads_real_config() -> None:
    """Scenario 1: the shipped config files load and validate correctly."""
    manager = ConfigManager(config_dir=REAL_CONFIG_DIR)
    assert manager.setup.version == "1.00"
    assert manager.setup.game.grid_size == [5, 5]
    assert manager.setup.scoring.cop_win == 20
    assert manager.setup.scoring.thief_win == 10
    assert "deepseek" in manager.rate_limits.rate_limits.services
    assert manager.logging.version == 1


def test_version_mismatch_raises(tmp_path: Path) -> None:
    """Scenario 2: a 0.99 setup version triggers ConfigurationVersionError."""
    bad = _valid_setup()
    bad["version"] = "0.99"
    config_dir = _write_config_dir(tmp_path, setup=bad)
    with pytest.raises(ConfigurationVersionError):
        ConfigManager(config_dir=config_dir)


def test_missing_required_key_raises(tmp_path: Path) -> None:
    """Scenario 3: removing a required key triggers Pydantic ValidationError."""
    bad = _valid_setup()
    del bad["scoring"]
    config_dir = _write_config_dir(tmp_path, setup=bad)
    with pytest.raises(ValidationError):
        ConfigManager(config_dir=config_dir)
