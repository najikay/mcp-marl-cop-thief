"""GameLoopController — runs sub-games and the full 6-sub-game game.

This is the MCP-Client / game engine in miniature: it arbitrates turns, routes
each agent's free-NL narration, enforces rules, applies the deterministic
transition, scores outcomes and accumulates totals. The natural-language
messages produced here are what the MCP servers will later carry over the wire.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field

from ..config.models import GameConfig
from ..constants import AgentRole, Direction, SubGameOutcome
from ..domain.action import Action
from ..domain.agents import CopAgent, ThiefAgent
from ..domain.board_state import BoardStateMachine
from ..domain.grid import Grid
from ..domain.rules import RulesEngine
from ..domain.scoring import ScoringEngine


@dataclass
class SubGameRecord:
    """Outcome and transcript of one sub-game."""

    index: int
    outcome: SubGameOutcome
    cop_score: int
    thief_score: int
    moves: int
    transcript: list[str] = field(default_factory=list)


@dataclass
class GameResult:
    """Aggregated result of a full game (``num_games`` valid sub-games)."""

    sub_games: list[SubGameRecord]
    cop_total: int
    thief_total: int


class GameLoopController:
    """Owns the turn loop. Pure orchestration — no external IO."""

    def __init__(self, config: GameConfig, cop: CopAgent, thief: ThiefAgent) -> None:
        self._config = config
        self._cop = cop
        self._thief = thief
        rows, cols = config.grid_size
        self._grid = Grid(rows, cols)
        self._rules = RulesEngine(self._grid, config.max_moves)
        self._machine = BoardStateMachine(self._grid, config.max_barriers)
        self._scoring = ScoringEngine(config.scoring)

    def play_game(self, rng: random.Random | None = None) -> GameResult:
        """Play ``num_games`` valid sub-games, re-running any technical voids."""
        rng = rng or random.Random(self._config.seed)
        records = self.play_sub_games(self._config.num_games, rng)
        cop_total = sum(r.cop_score for r in records)
        thief_total = sum(r.thief_score for r in records)
        return GameResult(sub_games=records, cop_total=cop_total, thief_total=thief_total)

    def play_sub_games(self, count: int, rng: random.Random) -> list[SubGameRecord]:
        """Play ``count`` valid sub-games, re-running any technical voids."""
        records: list[SubGameRecord] = []
        while len(records) < count:
            record = self._play_sub_game(len(records) + 1, rng)
            if record.outcome is not SubGameOutcome.VOID_TECHNICAL:
                records.append(record)
        return records

    def record_sub_game(self, rng: random.Random | None = None, on_step=None) -> SubGameRecord:
        """Play one sub-game, invoking ``on_step(state, message)`` per move (for a GUI)."""
        return self._play_sub_game(1, rng or random.Random(self._config.seed), on_step)

    def _play_sub_game(self, index: int, rng: random.Random, on_step=None) -> SubGameRecord:
        state = self._machine.initial_state(self._config.random_start, rng)
        mover = self._rules.first_mover()
        self._cop.reset()
        self._thief.reset()
        transcript: list[str] = []
        last_message: str | None = None
        if on_step is not None:
            on_step(state, None)  # initial frame
        outcome = self._rules.terminal_check(state)
        while outcome is None:
            agent = self._cop if mover is AgentRole.COP else self._thief
            agent.observe(last_message)  # perceive opponent only via free NL
            turn = agent.take_turn(state, self._rules)
            action = turn.action
            if not self._rules.validate(state, action):
                action = Action.move(mover, Direction.STAY)  # safe fallback
            state = self._machine.apply(state, action)
            transcript.append(turn.message)
            last_message = turn.message
            if on_step is not None:
                on_step(state, turn.message)
            outcome = self._resolve(mover, state)
            mover = self._rules.next_mover(mover)
        cop_score, thief_score = self._scoring.score(outcome)
        return SubGameRecord(index, outcome, cop_score, thief_score, state.move_count, transcript)

    def _resolve(self, mover: AgentRole, state) -> SubGameOutcome | None:
        """Capture only counts on the Cop's arrival; evasion on round timeout."""
        if mover is AgentRole.COP and self._rules.is_capture(state):
            return SubGameOutcome.COP_WINS
        if self._rules.moves_exhausted(state, self._config.max_moves):
            return SubGameOutcome.THIEF_WINS
        return None


def record_sub_game_frames(controller: GameLoopController, rng=None) -> list[dict]:
    """Play one sub-game and collect per-move frames (positions + message)."""
    frames: list[dict] = []

    def capture(state, message) -> None:
        frames.append(
            {
                "cop": [state.cop.row, state.cop.col],
                "thief": [state.thief.row, state.thief.col],
                "barriers": [[c.row, c.col] for c in state.barriers],
                "message": message,
            }
        )

    controller.record_sub_game(rng, capture)
    return frames
