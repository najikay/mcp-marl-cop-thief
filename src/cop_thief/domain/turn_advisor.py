"""turn_advisor — decide one agent's turn from its own cell and current belief.

An MCP agent server knows only its own position and what it has inferred from the
opponent's natural-language messages (a :class:`BeliefUpdate`). This helper turns
that into a single legal move plus the outgoing free-NL message, so a server can
answer ``propose_action`` without touching the authoritative board.
"""

from __future__ import annotations

from ..config.models import GameConfig
from ..constants import AgentRole
from .board_state import BoardState
from .grid import Cell, Grid
from .nl import BeliefUpdate, NLEncoder
from .rules import RulesEngine
from .strategy import BeliefHeuristicStrategy


def propose_turn(
    config: GameConfig,
    encoder: NLEncoder,
    self_cell: tuple[int, int],
    role: str,
    belief: BeliefUpdate | None = None,
) -> dict:
    """Return ``{action, direction, message, next_cell}`` for the agent's turn."""
    rows, cols = config.grid_size
    agent_role = AgentRole(role)
    rules = RulesEngine(Grid(rows, cols), config.max_moves)
    origin = Cell(*self_cell)
    state = BoardState(cop=origin, thief=origin, barriers_left=config.max_barriers)
    action = BeliefHeuristicStrategy().choose_action(state, agent_role, rules, belief)
    nxt = origin.step(action.direction)
    if not rules.grid.in_bounds(nxt):
        nxt = origin  # clamp; the orchestrator remains authoritative
    message = encoder.describe(origin, rows, cols, agent_role, action.direction)
    return {
        "action": action.kind.value,
        "direction": action.direction.name,
        "message": message,
        "next_cell": [nxt.row, nxt.col],
    }
