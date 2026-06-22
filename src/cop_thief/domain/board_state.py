"""BoardState and BoardStateMachine — the Dec-POMDP ``S`` and ``P``.

``BoardState`` is an immutable snapshot of the full world; ``BoardStateMachine``
produces the initial state and the copy-on-write transition ``apply`` that maps
``(state, action) -> state'`` deterministically.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field, replace

from ..constants import ActionType, AgentRole
from .action import Action
from .grid import Cell, Grid


@dataclass(frozen=True)
class BoardState:
    """Full board snapshot: agent positions, barriers and counters."""

    cop: Cell
    thief: Cell
    barriers: frozenset[Cell] = field(default_factory=frozenset)
    barriers_left: int = 0
    move_count: int = 0

    def is_blocked(self, cell: Cell) -> bool:
        """True if ``cell`` is sealed by a barrier."""
        return cell in self.barriers


class BoardStateMachine:
    """Builds initial states and applies the deterministic transition ``P``."""

    def __init__(self, grid: Grid, max_barriers: int) -> None:
        self._grid = grid
        self._max_barriers = max_barriers

    def initial_state(self, random_start: bool, rng: random.Random) -> BoardState:
        """Place cop and thief on distinct cells (random or far-apart corners)."""
        if random_start:
            cop, thief = self._random_distinct(rng)
        else:
            cells = self._grid.cells()
            cop, thief = cells[0], cells[-1]
        return BoardState(cop=cop, thief=thief, barriers_left=self._max_barriers)

    def _random_distinct(self, rng: random.Random) -> tuple[Cell, Cell]:
        cells = self._grid.cells()
        cop = rng.choice(cells)
        thief = rng.choice([c for c in cells if c != cop])
        return cop, thief

    def apply(self, state: BoardState, action: Action) -> BoardState:
        """Return the next state after ``action`` (assumes prior validation)."""
        actor = state.cop if action.role is AgentRole.COP else state.thief
        if action.kind is ActionType.PLACE_BARRIER:
            return self._place_barrier(state, actor)
        return self._move(state, action, actor)

    def _move(self, state: BoardState, action: Action, actor: Cell) -> BoardState:
        target = actor.step(action.direction)
        if not self._grid.in_bounds(target) or state.is_blocked(target):
            target = actor  # clamp illegal move to a STAY
        if action.role is AgentRole.COP:
            return replace(state, cop=target, move_count=state.move_count + 1)
        return replace(state, thief=target, move_count=state.move_count + 1)

    def _place_barrier(self, state: BoardState, actor: Cell) -> BoardState:
        barriers = state.barriers | {actor}
        return replace(
            state,
            barriers=barriers,
            barriers_left=state.barriers_left - 1,
            move_count=state.move_count + 1,
        )
