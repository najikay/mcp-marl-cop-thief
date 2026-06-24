"""Shared `request_move` resolver — the move an MCP server returns when challenged.

Rebuilds the board from the challenger's observation, picks the role's move with the
Conway-aware pursuit heuristic, and returns it as treaty prose. Barrier deployment
(ex06 §4.3 — the Cop walls its own current cell) is a planned tactic owned by the
strategy layer; it is not auto-emitted here.
"""

from __future__ import annotations

from cop_thief.domain.constants import AgentRole
from cop_thief.domain.grid import Grid
from cop_thief.domain.move_language import encode_move
from cop_thief.domain.state import DecPomdpGameState
from cop_thief.domain.strategy.heuristic import pursuit_target


def build_state(observation: dict) -> tuple[DecPomdpGameState, AgentRole, tuple]:
    """Rebuild ``(state, role, our_pos)`` from a challenger's observation dict."""
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
    return state, role, pos


def resolve_move(observation: dict) -> str:
    """Return the deterministic geometry move (treaty prose) for an observation."""
    state, role, pos = build_state(observation)
    return encode_move(role, pos, pursuit_target(state, role))
