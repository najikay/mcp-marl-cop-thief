"""Decision strategies for choosing a legal action from a board state."""

from .base_strategy import BaseStrategy
from .heuristic_strategy import HeuristicStrategy

__all__ = ["BaseStrategy", "HeuristicStrategy"]
