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

        Edge case: ``PLACE_BARRIER`` is a *barrier-move* — the Cop walls the cell it
        vacates (``self.cop_pos``) and steps to ``target`` (a barrier never holds an
        agent), decrementing its budget. A ``MOVE`` simply relocates the acting agent.
        The original instance is left pristine.
        """
        grid, cop, thief = self.grid, self.cop_pos, self.thief_pos
        barriers_left = self.cop_barriers_left
        if action_type is ActionType.PLACE_BARRIER:
            if role is AgentRole.COP and barriers_left > 0 and self.is_barrier_legal(target):
                grid = grid.model_copy(update={"barriers": grid.barriers | {self.cop_pos}})
                barriers_left -= 1
                cop = target  # vacate the now-walled cell — no agent stands on a barrier
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

    def is_barrier_legal(self, target: Coord) -> bool:
        """ex06 §4.3 barrier-move: wall the Cop's current cell and step it to ``target``.

        ``target`` must be a **distinct**, legal King step — the Cop must vacate the cell it
        walls, because a barrier is impassable to both agents (no one may stand on it).
        """
        return target != self.cop_pos and self.grid.is_legal_move(self.cop_pos, target)

    def legal_moves(self, role: AgentRole) -> list[Coord]:
        """Non-STAY legal destinations for ``role`` (an empty list means trapped)."""
        pos = self.cop_pos if role is AgentRole.COP else self.thief_pos
        return [c for c in get_adjacent_coords(pos, self.grid.shape) if self.grid.is_legal_move(pos, c)]
