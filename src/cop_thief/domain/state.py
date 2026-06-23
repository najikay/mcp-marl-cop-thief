"""Immutable Dec-POMDP game-state container with fog-of-war projection.

The state is a frozen Pydantic model. Every transition returns a brand-new
cloned instance and never mutates ``self`` — a hard requirement for the Phase-4
Monte-Carlo / Q-learning tree searches that explore many hypothetical futures
from a single shared root state.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from cop_thief.domain.constants import ActionType, AgentRole
from cop_thief.domain.geometry import calculate_manhattan, get_adjacent_coords
from cop_thief.domain.grid import Grid

Coord = tuple[int, int]


class DecPomdpGameState(BaseModel):
    """Full, immutable snapshot of the board at one turn."""

    model_config = ConfigDict(frozen=True)

    cop_pos: Coord
    thief_pos: Coord
    grid: Grid = Field(default_factory=Grid)
    turn_counter: int = 0
    cop_barriers_left: int = 5
    turn_role: AgentRole = AgentRole.THIEF

    @staticmethod
    def _sector(origin: Coord, target: Coord) -> str:
        """Return the qualitative quadrant of ``target`` relative to ``origin``."""
        d_row, d_col = target[0] - origin[0], target[1] - origin[1]
        vertical = "NORTH" if d_row < 0 else "SOUTH" if d_row > 0 else ""
        horizontal = "WEST" if d_col < 0 else "EAST" if d_col > 0 else ""
        return f"{vertical}{horizontal}" or "SAME"

    def get_subjective_observation(
        self, role: AgentRole, vision_radius: int = 2
    ) -> dict:
        """Project the true state onto one agent's partial observation (fog of war).

        If the opponent is within ``vision_radius`` (Manhattan), the exact
        opponent coordinates are revealed; otherwise only a qualitative
        occlusion sector (e.g. ``"THIEF_IN_NORTHWEST_QUADRANT"``) is returned.
        The logic is symmetric for Cop and Thief.
        """
        if role is AgentRole.COP:
            self_pos, opp_pos, opponent = self.cop_pos, self.thief_pos, "THIEF"
        else:
            self_pos, opp_pos, opponent = self.thief_pos, self.cop_pos, "COP"
        visible = calculate_manhattan(self_pos, opp_pos) <= vision_radius
        return {
            "role": role.value,
            "self_pos": self_pos,
            "turn": self.turn_counter,
            "opponent_visible": visible,
            "opponent_pos": opp_pos if visible else None,
            "opponent_sector": None
            if visible
            else f"{opponent}_IN_{self._sector(self_pos, opp_pos)}_QUADRANT",
        }

    def apply_action(
        self, role: AgentRole, action_type: ActionType, target: Coord
    ) -> DecPomdpGameState:
        """Return a NEW state with ``action`` applied; never mutates ``self``.

        Edge case: ``PLACE_BARRIER`` clones the grid with the target added and
        decrements the Cop's remaining barrier budget. A ``MOVE`` relocates the
        acting agent. The original instance is left pristine.
        """
        grid, cop, thief = self.grid, self.cop_pos, self.thief_pos
        barriers_left = self.cop_barriers_left
        if action_type is ActionType.PLACE_BARRIER:
            if role is AgentRole.COP and barriers_left > 0 and self._barrier_ok(target):
                grid = grid.model_copy(update={"barriers": grid.barriers | {target}})
                barriers_left -= 1
        elif role is AgentRole.COP:
            cop = target
        else:
            thief = target
        next_role = AgentRole.COP if self.turn_role is AgentRole.THIEF else AgentRole.THIEF
        return self.model_copy(
            update={
                "cop_pos": cop,
                "thief_pos": thief,
                "grid": grid,
                "turn_counter": self.turn_counter + 1,
                "cop_barriers_left": barriers_left,
                "turn_role": next_role,
            }
        )

    def _barrier_ok(self, target: Coord) -> bool:
        """Adjacent Barrier Law: in-bounds, Chebyshev<=1 from Cop, free cell."""
        d_row, d_col = abs(self.cop_pos[0] - target[0]), abs(self.cop_pos[1] - target[1])
        return (
            self.grid.is_within_bounds(target)
            and max(d_row, d_col) <= 1
            and target not in self.grid.barriers
            and target != self.thief_pos
        )

    def legal_moves(self, role: AgentRole) -> list[Coord]:
        """Non-STAY legal destinations for ``role`` (an empty list means trapped)."""
        pos = self.cop_pos if role is AgentRole.COP else self.thief_pos
        return [c for c in get_adjacent_coords(pos, self.grid.shape) if self.grid.is_legal_move(pos, c)]
