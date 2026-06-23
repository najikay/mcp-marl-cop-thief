"""TDD unit tests for the tabular Q-Learning strategy."""

from __future__ import annotations

from cop_thief.domain.constants import AgentRole
from cop_thief.domain.state import DecPomdpGameState
from cop_thief.domain.strategy import QTableStrategy


def _state() -> DecPomdpGameState:
    return DecPomdpGameState(cop_pos=(2, 2), thief_pos=(0, 0))


def test_bellman_td_update() -> None:
    """observe() applies Q += alpha*(r + gamma*max' - Q) with terminal masking."""
    strat = QTableStrategy(grid_shape=(5, 5))
    state, nxt = _state(), DecPomdpGameState(cop_pos=(2, 1), thief_pos=(0, 0))
    s_idx = strat._state_index(state)
    strat._last = (s_idx, 0)
    strat.q[s_idx, 0] = 0.5
    strat.q[strat._state_index(nxt)] = 2.0  # max' = 2.0
    strat.observe(reward=-1.0, next_state=nxt, done=False)
    assert round(float(strat.q[s_idx, 0]), 4) == 0.53  # -1 + 0.9*2 - 0.5 = 0.3 ; +0.1*0.3

    strat._last = (s_idx, 1)
    strat.q[s_idx, 1] = 0.5
    strat.observe(reward=-1.0, next_state=nxt, done=True)  # bootstrap masked
    assert round(float(strat.q[s_idx, 1]), 4) == 0.35


def test_epsilon_decay_floor() -> None:
    """Epsilon anneals geometrically toward the configured floor."""
    strat = QTableStrategy(grid_shape=(5, 5))
    start = strat.epsilon
    strat.decay_epsilon()
    assert strat.epsilon < start
    for _ in range(5000):
        strat.decay_epsilon()
    assert strat.epsilon == strat.rl.epsilon_min


def test_exploit_when_informed() -> None:
    """With epsilon=0 and a dominant Q-value, the argmax target is chosen."""
    strat = QTableStrategy(grid_shape=(5, 5))
    strat.epsilon = 0.0
    state = _state()
    legal = strat._legal(state, AgentRole.COP)
    idx, target = legal[2]  # an arbitrary legal action
    strat.q[strat._state_index(state), idx] = 9.0
    assert strat.select_target(state, AgentRole.COP) == target


def test_fallback_when_uninformed() -> None:
    """With epsilon=0 and a flat Q-row, selection defers to the fallback."""
    strat = QTableStrategy(grid_shape=(5, 5))
    strat.epsilon = 0.0
    state = _state()
    chosen = strat._legal(state, AgentRole.COP)[1][1]
    out = strat.select_target(state, AgentRole.COP, fallback=lambda s, r: chosen)
    assert out == chosen
