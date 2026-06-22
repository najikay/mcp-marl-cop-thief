"""Typed, versioned Q-Learning hyper-parameters (config-driven, PRD §E6).

Loaded from ``config/rl.json`` so no learning-rate or reward value is hardcoded
in the strategy. Ranges are clamped on construction (PLAN Phase 7.E).
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from .. import __version__

_DEFAULT_PATH = Path(__file__).resolve().parents[3] / "config" / "rl.json"


@dataclass(frozen=True)
class RLConfig:
    """Tabular Q-Learning settings: rates, exploration schedule and rewards."""

    version: str
    alpha: float
    gamma: float
    epsilon: float
    epsilon_min: float
    epsilon_decay: float
    reward_capture: float
    reward_step: float
    reward_escape: float

    @classmethod
    def from_dict(cls, data: dict) -> RLConfig:
        """Validate and construct, clamping rates to sane ranges."""
        config = cls(
            version=str(data.get("version", __version__)),
            alpha=_clamp(float(data["alpha"]), 0.0, 1.0),
            gamma=_clamp(float(data["gamma"]), 0.0, 1.0),
            epsilon=_clamp(float(data["epsilon"]), 0.0, 1.0),
            epsilon_min=_clamp(float(data["epsilon_min"]), 0.0, 1.0),
            epsilon_decay=_clamp(float(data["epsilon_decay"]), 0.0, 1.0),
            reward_capture=float(data["reward_capture"]),
            reward_step=float(data["reward_step"]),
            reward_escape=float(data["reward_escape"]),
        )
        return config


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def load_rl_config(path: str | Path | None = None) -> RLConfig:
    """Read and validate the RL config file."""
    target = Path(path) if path is not None else _DEFAULT_PATH
    if not target.exists():
        raise FileNotFoundError(f"rl config not found: {target}")
    return RLConfig.from_dict(json.loads(target.read_text(encoding="utf-8")))
