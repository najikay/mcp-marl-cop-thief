"""Shared `request_move` resolver — the move an MCP server returns when challenged.

Rebuilds the board from the challenger's observation, picks the role's action with
the Conway-aware pursuit heuristic, and returns it as treaty prose. The Cop will
deploy a barrier (instead of moving) when sealing a cornered Thief's escape route
is legal and capture is not already available this turn.
"""

from __future__ import annotations

from cop_thief.domain.constants import AgentRole
from cop_thief.domain.grid import Grid
from cop_thief.domain.move_language import encode_barrier, encode_move
from cop_thief.domain.state import DecPomdpGameState
from cop_thief.domain.strategy.heuristic import barrier_target, pursuit_target


def resolve_move(observation: dict) -> str:
    """Return this server's next action (treaty prose) for the given observation."""
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
        cop_barriers_left=int(observation.get("barriers_left", 5)),
    )
    pos = state.cop_pos if role is AgentRole.COP else state.thief_pos
    pursuit = pursuit_target(state, role)
    if role is AgentRole.COP and pursuit != state.thief_pos:
        seal = barrier_target(state)
        if seal is not None:
            return encode_barrier(role, pos, seal)
    return encode_move(role, pos, pursuit)
