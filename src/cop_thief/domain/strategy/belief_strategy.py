"""BeliefHeuristicStrategy — faithful partial-observability pursuit/evasion.

The agent acts only on the :class:`BeliefUpdate` parsed from the opponent's
natural-language message — never the opponent's true cell. The pursuer (Cop)
adds two tricks so it stops stalling on a coarse guess:

* **lead** the evader by the flee direction it announced, and
* **sweep** the board when it has reached its (stale) guess without a capture,

cycling through corners/centre until a fresh message sharpens the belief. The
evader (Thief) simply opens distance from the believed pursuer cell.
"""

from __future__ import annotations

from ...constants import AgentRole
from ..grid import Cell
from .base_strategy import BaseStrategy
from .heuristic_strategy import best_direction_toward, chebyshev


class BeliefHeuristicStrategy(BaseStrategy):
    """Decide using only the inferred belief about the opponent's region."""

    def __init__(self) -> None:
        self._sweep = 0

    def choose_action(self, state, role, rules, belief=None):
        """Pursue/evade the believed opponent cell, not the true one."""
        pursue = role is AgentRole.COP
        origin = state.cop if pursue else state.thief
        target = self._target(belief, rules, origin, pursue)
        direction = best_direction_toward(
            origin, target, pursue, state, rules, allow_stay=not pursue
        )
        from ..action import Action

        return Action.move(role, direction)

    def _target(self, belief, rules, origin: Cell, pursue: bool) -> Cell:
        """Where to head: believed opponent cell, led/swept for a pursuer."""
        cell = belief.estimate_cell(rules.grid) if belief is not None else None
        if cell is None:
            return self._centre(rules)
        if not pursue:
            return cell  # evader flees the believed pursuer cell
        led = self._lead(cell, belief)
        if chebyshev(origin, led) == 0:
            return self._sweep_target(rules)  # reached a stale guess -> search
        return led

    @staticmethod
    def _lead(cell: Cell, belief) -> Cell:
        """Aim one step ahead along the evader's announced flee direction."""
        if belief is not None and belief.moved is not None:
            dr, dc = belief.moved.vector
            return Cell(cell.row + dr, cell.col + dc)
        return cell

    @staticmethod
    def _centre(rules) -> Cell:
        return Cell(rules.grid.rows // 2, rules.grid.cols // 2)

    def _sweep_target(self, rules) -> Cell:
        """Rotate through corners and centre to cover ground between messages."""
        rows, cols = rules.grid.rows, rules.grid.cols
        spots = [
            Cell(0, 0),
            Cell(0, cols - 1),
            Cell(rows - 1, cols - 1),
            Cell(rows - 1, 0),
            self._centre(rules),
        ]
        self._sweep = (self._sweep + 1) % len(spots)
        return spots[self._sweep]
