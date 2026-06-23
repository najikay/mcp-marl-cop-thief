"""TDD unit tests for V1.1 bedrock: 8-way geometry, barrier law, trapped-death."""

from __future__ import annotations

from cop_thief.domain.agent import HARD_ARMOR, harden
from cop_thief.domain.constants import ActionType, AgentRole, SubGameOutcome
from cop_thief.domain.grid import Grid
from cop_thief.domain.state import DecPomdpGameState
from cop_thief.sdk.services import MatchCoordinator


def test_8way_king_movement_center_has_eight_moves() -> None:
    """A central cell on an open board yields all 8 King (Chebyshev) moves."""
    state = DecPomdpGameState(cop_pos=(2, 2), thief_pos=(4, 4))
    assert len(state.legal_moves(AgentRole.COP)) == 8


def test_adjacent_barrier_law() -> None:
    """Barriers drop only on Chebyshev<=1 free cells; far/occupied are no-ops."""
    state = DecPomdpGameState(cop_pos=(2, 2), thief_pos=(4, 4))
    near = state.apply_action(AgentRole.COP, ActionType.PLACE_BARRIER, (2, 3))
    assert (2, 3) in near.grid.barriers and near.cop_barriers_left == 4
    far = state.apply_action(AgentRole.COP, ActionType.PLACE_BARRIER, (4, 4))
    assert far.grid.barriers == frozenset() and far.cop_barriers_left == 5


def test_thief_trapped_is_cop_win() -> None:
    """A boxed-in Thief on its turn resolves to THIEF_TRAPPED (a Cop win)."""
    grid = Grid(shape=(5, 5), barriers=frozenset({(0, 1), (1, 0), (1, 1)}))
    state = DecPomdpGameState(cop_pos=(3, 3), thief_pos=(0, 0), grid=grid, turn_role=AgentRole.THIEF)
    assert MatchCoordinator(max_moves=25).evaluate_terminal_condition(state) is SubGameOutcome.THIEF_TRAPPED


def test_cop_trapped_yields_thief_win() -> None:
    """A boxed-in Cop on its turn can never capture, so the Thief wins."""
    grid = Grid(shape=(5, 5), barriers=frozenset({(0, 1), (1, 0), (1, 1)}))
    state = DecPomdpGameState(cop_pos=(0, 0), thief_pos=(3, 3), grid=grid, turn_role=AgentRole.COP)
    assert MatchCoordinator(max_moves=25).evaluate_terminal_condition(state) is SubGameOutcome.THIEF_WINS


def test_prompt_hard_armor_prepended() -> None:
    """harden() prefixes the unyielding security mandate to a system prompt."""
    out = harden("ENCODER RULES")
    assert out.startswith(HARD_ARMOR)
    assert "CRITICAL MANDATE" in out and "ENCODER RULES" in out
