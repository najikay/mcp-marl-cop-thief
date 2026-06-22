"""Typed, validated configuration models.

Every game parameter lives here as a typed field with no hardcoded gameplay
literal elsewhere. Scoring values are loaded from config and treated as
immutable at runtime (see PRD §3.4).
"""

from __future__ import annotations

from dataclasses import dataclass

CONFIG_VERSION = "1.0.0"


@dataclass(frozen=True)
class ScoringConfig:
    """The immutable per-sub-game scoring matrix."""

    cop_win: int
    thief_win: int
    cop_loss: int
    thief_loss: int

    @classmethod
    def from_dict(cls, data: dict) -> ScoringConfig:
        """Build from a raw ``scoring`` mapping, rejecting missing keys."""
        try:
            return cls(
                cop_win=int(data["cop_win"]),
                thief_win=int(data["thief_win"]),
                cop_loss=int(data["cop_loss"]),
                thief_loss=int(data["thief_loss"]),
            )
        except KeyError as exc:  # missing required key
            raise ValueError(f"scoring config missing key: {exc}") from exc


@dataclass(frozen=True)
class GameConfig:
    """Top-level game configuration, validated on construction."""

    version: str
    grid_size: tuple[int, int]
    max_moves: int
    num_games: int
    max_barriers: int
    random_start: bool
    seed: int | None
    scoring: ScoringConfig

    @classmethod
    def from_dict(cls, data: dict) -> GameConfig:
        """Validate and construct a :class:`GameConfig` from raw JSON data."""
        try:
            rows, cols = data["grid_size"]
        except (KeyError, ValueError) as exc:
            raise ValueError("grid_size must be a [rows, cols] pair") from exc
        config = cls(
            version=str(data.get("version", CONFIG_VERSION)),
            grid_size=(int(rows), int(cols)),
            max_moves=int(data["max_moves"]),
            num_games=int(data["num_games"]),
            max_barriers=int(data["max_barriers"]),
            random_start=bool(data.get("random_start", True)),
            seed=(None if data.get("seed") is None else int(data["seed"])),
            scoring=ScoringConfig.from_dict(data["scoring"]),
        )
        config._validate()
        return config

    def _validate(self) -> None:
        """Reject impossible game geometry/limits with a clear message."""
        rows, cols = self.grid_size
        if rows < 1 or cols < 1:
            raise ValueError(f"grid dimensions must be positive, got {self.grid_size}")
        if rows * cols < 2:
            raise ValueError("grid must hold at least two distinct cells")
        if self.max_moves < 1:
            raise ValueError("max_moves must be >= 1")
        if self.num_games < 1:
            raise ValueError("num_games must be >= 1")
        if self.max_barriers < 0:
            raise ValueError("max_barriers must be >= 0")
