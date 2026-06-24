"""Shared `request_move` resolver — the move an MCP server returns when challenged.

Rebuilds the board from the challenger's observation, picks the role's move with
the Conway-aware pursuit heuristic, and returns it as treaty prose.
"""

from __future__ import annotations

from cop_thief.domain.constants import AgentRole
from cop_thief.domain.grid import Grid
from cop_thief.domain.move_language import encode_move
from cop_thief.domain.state import DecPomdpGameState
from cop_thief.domain.strategy.heuristic import pursuit_target


def resolve_move(observation: dict) -> str:
    """Return this server's next move (treaty prose) for the given observation."""
    role = AgentRole(observation["role"])
    grid = Grid(
        shape=tuple(observation.get("grid", [5, 5])),
        barriers=frozenset(tuple(cell) for cell in observation.get("barriers", [])),
    )
    state = DecPomdpGameState(
        cop_pos=tuple(observation["cop"]),
        thief_pos=tuple(observation["thief"]),
        grid=grid,
        turn_role=role,
    )
    pos = state.cop_pos if role is AgentRole.COP else state.thief_pos
    return encode_move(role, pos, pursuit_target(state, role))
