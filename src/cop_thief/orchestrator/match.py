"""Match Orchestrator: a real, decentralized-style Cop-vs-Thief turn loop.

Drives thief-first turns, applies each agent's chosen move deterministically,
streams every turn to the live broadcast bus + audit log, and tallies a 3-match
game. Move selection reuses the Q/geometry strategy stack; NL prose is templated
with the treaty's [INTENT] signposts.
"""

from __future__ import annotations

import time

from cop_thief.domain.constants import ActionType, AgentRole, SubGameOutcome
from cop_thief.domain.geometry import is_conway_trap_inevitable
from cop_thief.domain.grid import Grid
from cop_thief.domain.move_language import encode_move
from cop_thief.domain.state import DecPomdpGameState
from cop_thief.domain.strategy.heuristic import pursuit_target
from cop_thief.sdk.services import MatchCoordinator


class MatchOrchestrator:
    """Run real matches and 3-match games, broadcasting + logging every turn."""

    def __init__(self, observer=None, logger=None, grid_size=5, max_moves=25, turn_delay=0.0):
        """Wire the live observer (broadcast bus), the audit logger and timing."""
        self._observer = observer
        self._logger = logger
        self._grid = grid_size
        self._coord = MatchCoordinator(max_moves=max_moves)
        self._delay = turn_delay

    def _initial_state(self) -> DecPomdpGameState:
        return DecPomdpGameState(
            cop_pos=(0, 0), thief_pos=(self._grid - 1, self._grid - 1),
            grid=Grid(shape=(self._grid, self._grid)),
        )

    def _emit(self, role: AgentRole, before: tuple, state: DecPomdpGameState, informed: bool) -> None:
        after = state.cop_pos if role is AgentRole.COP else state.thief_pos
        prose = encode_move(role, before, after)
        if self._observer is not None:
            self._observer(state, prose, informed)
        if self._logger is not None:
            conway = is_conway_trap_inevitable(
                state.cop_pos, state.thief_pos, set(state.grid.barriers), state.grid.shape
            )
            self._logger.log_turn(
                state.turn_counter,
                {"cop": list(state.cop_pos), "thief": list(state.thief_pos),
                 "barriers": [list(b) for b in state.grid.barriers]},
                prose if role is AgentRole.COP else "",
                prose if role is AgentRole.THIEF else "",
                informed, conway,
            )

    def play_match(self, cop_strategy, thief_strategy) -> SubGameOutcome:
        """Play one thief-first match to a terminal outcome."""
        state = self._initial_state()
        for _ in range(self._coord.max_moves * 2):
            outcome = self._coord.evaluate_terminal_condition(state)
            if outcome is not None:
                return outcome
            role = state.turn_role
            strategy = cop_strategy if role is AgentRole.COP else thief_strategy
            before = state.cop_pos if role is AgentRole.COP else state.thief_pos
            target = strategy.select_target(state, role, fallback=pursuit_target)
            informed = strategy.is_informed(state, role)
            state = state.apply_action(role, ActionType.MOVE, target)
            self._emit(role, before, state, informed)
            if self._delay:
                time.sleep(self._delay)
        return self._coord.evaluate_terminal_condition(state) or SubGameOutcome.THIEF_WINS

    def play_game(self, cop_roster, thief_roster) -> list[SubGameOutcome]:
        """Play a game = 3 matches (agent i vs agent i), returning the outcomes."""
        return [
            self.play_match(cop_roster.agent(i), thief_roster.agent(i))
            for i in range(len(cop_roster))
        ]
