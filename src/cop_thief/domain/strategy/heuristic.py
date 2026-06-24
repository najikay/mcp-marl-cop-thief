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


def barrier_target(state, reach: int = 2):
    """Return a cell the Cop should legally seal to cut a nearby Thief's escape, else None.

    Triggers only when the Thief is within Chebyshev ``reach`` and one of its escape
    cells is adjacent to the Cop (Adjacent Barrier Law) — sealing the escape route
    nearest the Thief drives toward a THIEF_TRAPPED win without wasting the budget.
    """
    if state.cop_barriers_left <= 0:
        return None
    cop, thief = state.cop_pos, state.thief_pos
    if max(abs(cop[0] - thief[0]), abs(cop[1] - thief[1])) > reach:
        return None
    escapes = set(state.legal_moves(AgentRole.THIEF))
    candidates = [
        c for c in get_adjacent_coords(cop, state.grid.shape)
        if c in escapes and state.is_barrier_legal(c)
    ]
    if not candidates:
        return None
    return min(candidates, key=lambda c: calculate_manhattan(c, thief))
