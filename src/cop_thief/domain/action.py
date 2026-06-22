"""Action — a single agent decision applied to the board state machine."""

from __future__ import annotations

from dataclasses import dataclass

from ..constants import ActionType, AgentRole, Direction


@dataclass(frozen=True)
class Action:
    """A move (with a direction) or a barrier placement by an agent.

    ``direction`` is required for :data:`ActionType.MOVE` and ignored for
    :data:`ActionType.PLACE_BARRIER` (the barrier seals the actor's own cell).
    """

    role: AgentRole
    kind: ActionType
    direction: Direction = Direction.STAY

    @classmethod
    def move(cls, role: AgentRole, direction: Direction) -> Action:
        """Construct a movement action."""
        return cls(role=role, kind=ActionType.MOVE, direction=direction)

    @classmethod
    def barrier(cls, role: AgentRole) -> Action:
        """Construct a barrier-placement action (Cop only; validated downstream)."""
        return cls(role=role, kind=ActionType.PLACE_BARRIER)
