"""Unit tests for the immutable enums and direction vectors."""

from __future__ import annotations

from cop_thief.constants import MOVE_PRIORITY, ActionType, AgentRole, Direction, SubGameOutcome


def test_direction_vectors_unique_and_stay_is_zero():
    vectors = [d.vector for d in Direction]
    assert Direction.STAY.vector == (0, 0)
    assert len(set(vectors)) == len(vectors)  # no duplicate direction vectors


def test_eight_moves_plus_stay():
    assert len(Direction) == 9


def test_move_priority_covers_every_direction():
    assert set(MOVE_PRIORITY) == set(Direction)


def test_role_and_action_enums():
    assert {r.value for r in AgentRole} == {"cop", "thief"}
    assert {a.value for a in ActionType} == {"move", "place_barrier"}
    assert SubGameOutcome.VOID_TECHNICAL.value == "void_technical"
