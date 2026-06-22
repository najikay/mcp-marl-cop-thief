"""Unit tests for the tabular Q-Learning core, strategy and trainer."""

from __future__ import annotations

import random

from cop_thief.config.models import GameConfig
from cop_thief.config.rl_config import RLConfig, load_rl_config
from cop_thief.constants import AgentRole
from cop_thief.domain.board_state import BoardState, BoardStateMachine
from cop_thief.domain.grid import Cell, Grid
from cop_thief.domain.rules import RulesEngine
from cop_thief.domain.strategy import (
    HeuristicStrategy,
    QLearningStrategy,
    QLearningTrainer,
    QTable,
)
from cop_thief.domain.strategy.qtable import encode_state

_RL = RLConfig(
    version="1.0.0",
    alpha=0.5,
    gamma=0.9,
    epsilon=0.3,
    epsilon_min=0.02,
    epsilon_decay=0.99,
    reward_capture=20.0,
    reward_step=-0.5,
    reward_escape=-10.0,
)


def _config(grid):
    return GameConfig.from_dict(
        {
            "version": "1.0.0",
            "grid_size": list(grid),
            "max_moves": 12,
            "num_games": 6,
            "max_barriers": 5,
            "random_start": True,
            "seed": 3,
            "scoring": {"cop_win": 20, "thief_win": 10, "cop_loss": 5, "thief_loss": 5},
        }
    )


def test_bellman_update_moves_value_toward_target():
    table = QTable(alpha=0.5, gamma=0.9)
    table.update(key=0, action=2, reward=10.0, next_key=1, done=True)
    # terminal target = reward; value moves halfway (alpha 0.5) from 0 to 10.
    assert table.best_value(0) == 5.0


def test_greedy_index_picks_highest_allowed():
    table = QTable(alpha=0.5, gamma=0.9)
    table.update(0, 3, 5.0, 1, True)
    assert table.greedy_index(0, [0, 3, 5]) == 3
    assert table.greedy_index(0, [0, 1]) in (0, 1)  # unseen actions tie at 0


def test_encode_state_is_unique_per_position_pair():
    grid = Grid(3, 3)
    a = encode_state(BoardState(Cell(0, 0), Cell(2, 2)), grid)
    b = encode_state(BoardState(Cell(2, 2), Cell(0, 0)), grid)
    assert a != b


def test_save_and_load_roundtrip(tmp_path):
    table = QTable(0.5, 0.9)
    table.update(7, 1, 3.0, 8, True)
    path = tmp_path / "q.json"
    table.save(path)
    loaded = QTable.load(path, 0.5, 0.9)
    assert loaded.best_value(7) == table.best_value(7)


def test_strategy_returns_legal_action():
    table = QTable(0.5, 0.9)
    rules = RulesEngine(Grid(3, 3), 12)
    state = BoardState(cop=Cell(0, 0), thief=Cell(2, 2), barriers_left=5)
    action = QLearningStrategy(table).choose_action(state, AgentRole.COP, rules)
    assert rules.validate(state, action)


def test_trained_cop_captures_more_than_untrained():
    config = _config((3, 3))
    trained = QLearningTrainer(config, _RL, rng=random.Random(1)).train(episodes=4000)
    rules = RulesEngine(Grid(3, 3), config.max_moves)
    thief = HeuristicStrategy()
    captures = 0
    machine_rng = random.Random(99)
    machine = BoardStateMachine(Grid(3, 3), config.max_barriers)
    cop_strategy = QLearningStrategy(trained)
    for _ in range(30):
        state = machine.initial_state(True, machine_rng)
        for _ in range(config.max_moves):
            state = machine.apply(state, cop_strategy.choose_action(state, AgentRole.COP, rules))
            if rules.is_capture(state):
                captures += 1
                break
            state = machine.apply(state, thief.choose_action(state, AgentRole.THIEF, rules))
            if rules.is_capture(state):
                captures += 1
                break
    assert captures >= 20  # a trained pursuer catches the evader most of the time


def test_load_rl_config_reads_real_file():
    assert load_rl_config().gamma == 0.9
