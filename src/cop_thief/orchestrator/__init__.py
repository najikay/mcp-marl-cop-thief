"""Orchestrator: drives the turn loop and aggregates results."""

from .bonus_series import BonusSeriesController, BonusSeriesResult, GroupSide
from .game_loop import GameLoopController, GameResult, SubGameRecord
from .mcp_client import MCPAgentClient
from .remote_game import RemoteGameController, run_remote_game

__all__ = [
    "BonusSeriesController",
    "BonusSeriesResult",
    "GameLoopController",
    "GameResult",
    "GroupSide",
    "MCPAgentClient",
    "RemoteGameController",
    "SubGameRecord",
    "run_remote_game",
]
