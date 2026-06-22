"""RemoteGameController — drive a game across two MCP servers over the wire.

This is the networked twin of :class:`GameLoopController`: the agents live behind
MCP servers and are reached only through their tools, exchanging free natural
language, while this orchestrator holds the **authoritative** board and applies
the rules and scoring. Works in-memory (tests) or against cloud URLs unchanged.
"""

from __future__ import annotations

import asyncio
import random

from ..config.models import GameConfig
from ..constants import ActionType, AgentRole, Direction, SubGameOutcome
from ..domain.action import Action
from ..domain.board_state import BoardStateMachine
from ..domain.grid import Grid
from ..domain.rules import RulesEngine
from ..domain.scoring import ScoringEngine
from .game_loop import GameResult, SubGameRecord
from .mcp_client import MCPAgentClient


class RemoteGameController:
    """Play a full game by driving two remote agent servers via MCP."""

    def __init__(
        self,
        config: GameConfig,
        cop_target,
        thief_target,
        cop_token: str | None = None,
        thief_token: str | None = None,
    ) -> None:
        self._config = config
        self._cop_target = cop_target
        self._thief_target = thief_target
        self._cop_token = cop_token
        self._thief_token = thief_token
        rows, cols = config.grid_size
        self._grid = Grid(rows, cols)
        self._rules = RulesEngine(self._grid, config.max_moves)
        self._machine = BoardStateMachine(self._grid, config.max_barriers)
        self._scoring = ScoringEngine(config.scoring)

    async def play_game(self, rng: random.Random | None = None) -> GameResult:
        """Connect to both servers and play ``num_games`` sub-games."""
        rng = rng or random.Random(self._config.seed)
        async with (
            MCPAgentClient(self._cop_target, self._cop_token) as cop,
            MCPAgentClient(self._thief_target, self._thief_token) as thief,
        ):
            records = []
            for index in range(1, self._config.num_games + 1):
                records.append(await self._play_sub_game(index, rng, cop, thief))
        cop_total = sum(r.cop_score for r in records)
        thief_total = sum(r.thief_score for r in records)
        return GameResult(records, cop_total, thief_total)

    async def _play_sub_game(self, index, rng, cop, thief) -> SubGameRecord:
        state = self._machine.initial_state(self._config.random_start, rng)
        sid = f"sub-{index}"
        await cop.start_sub_game(sid, [state.cop.row, state.cop.col])
        await thief.start_sub_game(sid, [state.thief.row, state.thief.col])
        mover = self._rules.first_mover()
        transcript: list[str] = []
        outcome = self._rules.terminal_check(state)
        while outcome is None:
            client = cop if mover is AgentRole.COP else thief
            other = thief if mover is AgentRole.COP else cop
            turn = await client.propose_action(sid)
            state = self._machine.apply(state, self._to_action(mover, turn, state))
            await other.receive_message(sid, turn["message"])
            transcript.append(turn["message"])
            outcome = self._resolve(mover, state)
            mover = self._rules.next_mover(mover)
        cop_score, thief_score = self._scoring.score(outcome)
        return SubGameRecord(index, outcome, cop_score, thief_score, state.move_count, transcript)

    def _to_action(self, role: AgentRole, turn: dict, state) -> Action:
        if turn.get("action") == ActionType.PLACE_BARRIER.value:
            barrier = Action.barrier(role)
            if self._rules.validate(state, barrier):
                return barrier
        move = Action.move(role, Direction[turn.get("direction", "STAY")])
        return move if self._rules.validate(state, move) else Action.move(role, Direction.STAY)

    def _resolve(self, mover: AgentRole, state) -> SubGameOutcome | None:
        if mover is AgentRole.COP and self._rules.is_capture(state):
            return SubGameOutcome.COP_WINS
        if self._rules.moves_exhausted(state, self._config.max_moves):
            return SubGameOutcome.THIEF_WINS
        return None


def run_remote_game(
    config: GameConfig,
    cop_target,
    thief_target,
    cop_token: str | None = None,
    thief_token: str | None = None,
) -> GameResult:
    """Synchronous convenience wrapper around :meth:`RemoteGameController.play_game`."""
    controller = RemoteGameController(config, cop_target, thief_target, cop_token, thief_token)
    return asyncio.run(controller.play_game())
