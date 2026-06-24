"""Conway-aware geometric pursuit heuristic (Tier-2 fallback).

Single source of truth shared by the GameLoopController and the MatchOrchestrator
(DRY): the Cop minimises Chebyshev distance (preferring inevitable traps); the
Thief maximises it.
"""

from __future__ import annotations

from cop_thief.domain.constants import AgentRole
from cop_thief.domain.geometry import (
    calculate_manhattan,
    get_adjacent_coords,
    is_conway_trap_inevitable,
)


def pursuit_target(state, role) -> tuple:
    """Return the geometry-optimal legal step for ``role`` (Cop pursue / Thief flee)."""
    pos = state.cop_pos if role is AgentRole.COP else state.thief_pos
    ref = state.thief_pos if role is AgentRole.COP else state.cop_pos
    legal = [c for c in get_adjacent_coords(pos, state.grid.shape) if state.grid.is_legal_move(pos, c)]
    if not legal:
        return pos
    if role is AgentRole.COP:
        barriers = set(state.grid.barriers)
        traps = [c for c in legal if is_conway_trap_inevitable(c, ref, barriers, state.grid.shape)]
        return min(traps or legal, key=lambda c: calculate_manhattan(c, ref))
    return max(legal, key=lambda c: calculate_manhattan(c, ref))
