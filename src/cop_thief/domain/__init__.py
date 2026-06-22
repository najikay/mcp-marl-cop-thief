"""Domain core: grid, state machine, rules and scoring (pure, no IO)."""

from .board_state import BoardState, BoardStateMachine
from .grid import Cell, Grid
from .scoring import ScoringEngine

__all__ = ["BoardState", "BoardStateMachine", "Cell", "Grid", "ScoringEngine"]
