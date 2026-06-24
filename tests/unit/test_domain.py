"""TDD unit tests for the Dec-POMDP core domain layer.

Four rigorous scenarios:
1. Conway trap detection — positive, escapable, and out-of-range negatives.
2. Grid out-of-bounds boundary enforcement and move legality.
3. Pure state immutability across ``apply_action`` (identity + value pristine).
4. Fog-of-war subjective masking (visible exact vs occluded sector, symmetric).
"""

from __future__ import annotations

from cop_thief.domain.constants import ActionType, AgentRole
from cop_thief.domain.geometry import is_conway_trap_inevitable
from cop_thief.domain.grid import Grid
from cop_thief.domain.state import DecPomdpGameState


def test_conway_trap_detection() -> None:
    """Positive trap, escapable layout, and out-of-range all classify correctly."""
    barriers = {(0, 1), (1, 0), (1, 1)}
    # Thief cornered at (0,0); all 3 in-bounds neighbours walled; cop 2 away.
    assert is_conway_trap_inevitable((0, 2), (0, 0), barriers, (5, 5)) is True
    # Open board: thief has escape vectors even though cop is close.
    assert is_conway_trap_inevitable((2, 4), (2, 2), set(), (5, 5)) is False
    # Cop too far (Manhattan 4 > 2): never an inevitable trap.
    assert is_conway_trap_inevitable((0, 4), (0, 0), barriers, (5, 5)) is False


def test_grid_bounds_and_move_legality() -> None:
    """Boundaries and barrier/step legality are enforced."""
    grid = Grid(shape=(5, 5), barriers=frozenset({(2, 2)}))
    assert grid.is_within_bounds((4, 4)) is True
    assert grid.is_within_bounds((5, 5)) is False
    assert grid.is_within_bounds((-1, 0)) is False
    assert grid.is_barrier((2, 2)) is True
    assert grid.is_legal_move((2, 3), (2, 2)) is False  # into a barrier
    assert grid.is_legal_move((3, 3), (4, 4)) is True   # diagonal step
    assert grid.is_legal_move((0, 0), (2, 2)) is False  # too far (>1)


def test_state_immutability_after_apply_action() -> None:
    """apply_action returns a new object and leaves the original pristine."""
    state = DecPomdpGameState(cop_pos=(0, 0), thief_pos=(4, 4))
    original_id = id(state)
    original_cop = state.cop_pos

    moved = state.apply_action(AgentRole.COP, ActionType.MOVE, (1, 1))
    assert moved is not state
    assert id(state) == original_id
    assert state.cop_pos == original_cop == (0, 0)
    assert state.turn_counter == 0
    assert moved.cop_pos == (1, 1)
    assert moved.turn_counter == 1

    walled = state.apply_action(AgentRole.COP, ActionType.PLACE_BARRIER, (1, 1))  # §4.3 barrier-move
    assert state.grid.barriers == frozenset()          # original untouched
    assert (0, 0) in walled.grid.barriers              # the vacated cell is walled
    assert walled.cop_pos == (1, 1)                    # the Cop stepped off it
    assert walled.cop_barriers_left == 4

    fled = state.apply_action(AgentRole.THIEF, ActionType.MOVE, (3, 3))
    assert fled is not state
    assert state.thief_pos == (4, 4)                    # original untouched
    assert fled.thief_pos == (3, 3)
    assert fled.cop_pos == (0, 0)


def test_fog_of_war_subjective_masking() -> None:
    """Close opponents reveal exact coords; distant ones only a sector."""
    near = DecPomdpGameState(cop_pos=(2, 2), thief_pos=(2, 3))
    near_obs = near.get_subjective_observation(AgentRole.COP, vision_radius=2)
    assert near_obs["opponent_visible"] is True
    assert near_obs["opponent_pos"] == (2, 3)
    assert near_obs["opponent_sector"] is None

    far = DecPomdpGameState(cop_pos=(0, 0), thief_pos=(4, 4))
    cop_obs = far.get_subjective_observation(AgentRole.COP, vision_radius=2)
    assert cop_obs["opponent_visible"] is False
    assert cop_obs["opponent_pos"] is None
    assert cop_obs["opponent_sector"] == "THIEF_IN_SOUTHEAST_QUADRANT"

    thief_obs = far.get_subjective_observation(AgentRole.THIEF, vision_radius=2)
    assert thief_obs["opponent_sector"] == "COP_IN_NORTHWEST_QUADRANT"
