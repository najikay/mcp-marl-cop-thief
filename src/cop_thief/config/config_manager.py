"""ConfigManager — the single source of truth for game parameters.

Loads a versioned JSON file and exposes a validated :class:`GameConfig`. The
code version is checked against the config version to fail fast on mismatch.
"""

from __future__ import annotations

import json
from pathlib import Path

from .. import __version__
from .models import GameConfig

_DEFAULT_CONFIG_PATH = Path(__file__).resolve().parents[3] / "config" / "setup.json"


class ConfigManager:
    """Load and validate game configuration from a JSON file."""

    def __init__(self, path: str | Path | None = None) -> None:
        self._path = Path(path) if path is not None else _DEFAULT_CONFIG_PATH
        self._config: GameConfig | None = None

    def load(self) -> GameConfig:
        """Read, parse and validate the config file (cached after first call)."""
        if self._config is not None:
            return self._config
        if not self._path.exists():
            raise FileNotFoundError(f"config file not found: {self._path}")
        try:
            raw = json.loads(self._path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise ValueError(f"malformed config JSON in {self._path}: {exc}") from exc
        config = GameConfig.from_dict(raw)
        self._guard_version(config)
        self._config = config
        return config

    @staticmethod
    def _guard_version(config: GameConfig) -> None:
        """Fail fast if the config version diverges from the code version."""
        if config.version != __version__:
            raise ValueError(
                f"version mismatch: code {__version__} != config {config.version}"
            )
