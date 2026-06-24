"""TDD: opponent-rationality model, the risk/expectimax knob, and random openings."""

from __future__ import annotations

import random

from cop_thief.domain.constants import AgentRole
from cop_thief.domain.geometry import random_start_positions
from cop_thief.domain.state import DecPomdpGameState
from cop_thief.domain.strategy.minimax import MinimaxPlanner
from cop_thief.domain.strategy.opponent import OpponentModel, opponent_was_rational


def test_opponent_model_pessimism_tracks_rationality() -> None:
    """No data → pessimism 1.0 (safe); otherwise the observed rational-rate."""
    model = OpponentModel()
    assert model.pessimism() == 1.0
    for verdict in (True, True, False, False):
        model.observe(verdict)
    assert model.pessimism() == 0.5


def test_opponent_was_rational_judges_flee_and_chase() -> None:
    """A fleeing Thief and a closing Cop read as rational; the opposite as not."""
    assert opponent_was_rational("cop", {"cop": [2, 2], "thief": [2, 3]}, {"cop": [2, 2], "thief": [2, 4]})
    assert not opponent_was_rational("cop", {"cop": [2, 2], "thief": [2, 4]}, {"cop": [2, 2], "thief": [2, 3]})
    assert opponent_was_rational("thief", {"cop": [1, 1], "thief": [4, 4]}, {"cop": [2, 2], "thief": [4, 4]})
    assert not opponent_was_rational("thief", {"cop": [2, 2], "thief": [4, 4]}, {"cop": [1, 1], "thief": [4, 4]})


def test_pessimism_knob_accepted_and_capture_still_optimal() -> None:
    """The planner accepts any pessimism and still takes a guaranteed capture."""
    planner = MinimaxPlanner(depth=2)
    far = DecPomdpGameState(cop_pos=(0, 0), thief_pos=(4, 4), turn_role=AgentRole.COP)
    for pessimism in (0.0, 0.5, 1.0):
        assert planner.best_action(far, pessimism=pessimism)[0] is not None
    adjacent = DecPomdpGameState(cop_pos=(2, 2), thief_pos=(2, 3), turn_role=AgentRole.COP)
    assert planner.best_action(adjacent, pessimism=0.0)[1] == (2, 3)


def test_random_start_positions_distinct_and_in_bounds() -> None:
    """Seeded openings yield two distinct in-bounds cells (ex06 §4.2 random start)."""
    rng = random.Random(0)
    for _ in range(25):
        cop, thief = random_start_positions(5, 5, rng)
        assert cop != thief
        assert all(0 <= p[0] < 5 and 0 <= p[1] < 5 for p in (cop, thief))


def test_random_start_is_reproducible_per_seed() -> None:
    """Identical seeds reproduce identical openings (so both groups agree)."""
    assert random_start_positions(5, 5, random.Random(7)) == random_start_positions(5, 5, random.Random(7))
