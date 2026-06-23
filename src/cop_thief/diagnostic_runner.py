"""Sterile, zero-cost diagnostic probe for the turn-progression loop.

Runs the real GameLoopController with MOCKED LLM encoder/parser (no network) over
a hardcoded 5x5 state: a silent 400-episode Q-warmup, then a greedy 10-turn
pursuit printing per-turn telemetry and flagging STAY-while-not-boxed failures.
"""

from __future__ import annotations

import random
import tempfile
from pathlib import Path
from unittest import mock

from cop_thief.domain.constants import AgentRole, Direction
from cop_thief.domain.geometry import get_adjacent_coords, is_conway_trap_inevitable
from cop_thief.domain.grid import Grid
from cop_thief.domain.state import DecPomdpGameState
from cop_thief.orchestrator.controller import GameLoopController
from cop_thief.orchestrator.firewall import CognitiveFirewall
from cop_thief.orchestrator.models import BeliefUpdate
from cop_thief.sdk import CopThiefSDK

_RED = "\033[91m"
_RESET = "\033[0m"
_WARMUP_EPISODES = 400
_LABELS = {(-1, 0): "UP", (1, 0): "DOWN", (0, -1): "LEFT", (0, 1): "RIGHT",
           (-1, -1): "UP-LEFT", (-1, 1): "UP-RIGHT", (1, -1): "DOWN-LEFT",
           (1, 1): "DOWN-RIGHT", (0, 0): "STAY"}


def _belief() -> BeliefUpdate:
    return BeliefUpdate(estimated_direction=Direction.STAY, distance_band="UNKNOWN", inferred_barriers=frozenset(), confidence_score=0.0)


def _label(before: tuple, after: tuple) -> str:
    return _LABELS.get((after[0] - before[0], after[1] - before[1]), "??")


def _boxed_in(state: DecPomdpGameState, pos: tuple) -> bool:
    return not [c for c in get_adjacent_coords(pos, state.grid.shape) if state.grid.is_legal_move(pos, c)]


def _warn(message: str) -> None:
    print(f"{_RED}>>> DIAGNOSTIC FAILURE: {message}{_RESET}")


def _build_controller() -> GameLoopController:
    encoder = mock.Mock()
    encoder.generate_prose_transmission = mock.Mock(return_value="(diagnostic prose)")
    parser = mock.Mock()
    parser.parse_inbound_prose = mock.Mock(return_value=_belief())
    ledger = Path(tempfile.gettempdir()) / "diag_ledger.json"
    ledger.unlink(missing_ok=True)
    sdk = CopThiefSDK()
    sdk.initialize_match()
    return GameLoopController(sdk=sdk, encoder=encoder, parser=parser, firewall=CognitiveFirewall(ledger_file=ledger))


def run_diagnostic() -> None:
    """Warm up the Q-table silently, then unroll a greedy 10-turn pursuit."""
    random.seed(0)  # deterministic, reproducible flight report
    controller = _build_controller()
    for _ in range(_WARMUP_EPISODES):
        controller.run_simulated_sub_game("warmup")
    print(f"[PRE-TRAIN WARMUP] {_WARMUP_EPISODES} episodes executed silently; epsilon now {controller._strategy.epsilon:.3f}")
    controller._strategy.epsilon = 0.0  # greedy exploitation for the flight demo
    state = DecPomdpGameState(cop_pos=(0, 0), thief_pos=(4, 4), grid=Grid(shape=(5, 5)))
    first_geometry_turn = None
    for turn in range(1, 11):
        cop_b, thief_b = state.cop_pos, state.thief_pos
        informed = controller._strategy.is_informed(state, AgentRole.COP)
        if not informed and first_geometry_turn is None:
            first_geometry_turn = turn
        state, _ = controller.execute_single_turn_cycle(state, "demo", "edging along")
        state, _ = controller.execute_single_turn_cycle(state, "demo", "edging along")
        cop_a, thief_a = _label(cop_b, state.cop_pos), _label(thief_b, state.thief_pos)
        conway = is_conway_trap_inevitable(state.cop_pos, state.thief_pos, set(state.grid.barriers), state.grid.shape)
        print(f"[Turn {turn:02d}/10] Cop:({state.cop_pos[0]},{state.cop_pos[1]}) Thief:({state.thief_pos[0]},{state.thief_pos[1]}) | CopAction: {cop_a} | ThiefAction: {thief_a} | ConwayTrap: {conway} | Informed: {informed}")
        if cop_a == "STAY" and not _boxed_in(state, cop_b):
            _warn(f"Turn {turn}: Cop chose STAY with legal moves available (violates K5).")
        if state.cop_pos == state.thief_pos:
            print(f"[OUTCOME] Valid grid capture on turn {turn}. first_geometry_turn={first_geometry_turn}")
            return
    _warn(f"Turn 10 limit hit with NO capture (first_geometry_turn={first_geometry_turn}); pursuit math still oscillating.")


if __name__ == "__main__":
    run_diagnostic()
