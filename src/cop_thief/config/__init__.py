"""Configuration layer: versioned, validated, single source of truth."""

from .config_manager import ConfigManager
from .models import GameConfig, ScoringConfig

__all__ = ["ConfigManager", "GameConfig", "ScoringConfig"]
