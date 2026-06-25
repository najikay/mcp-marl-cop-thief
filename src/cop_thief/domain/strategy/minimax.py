"""Risk-tunable minimax / expectimax over the zero-sum Markov game.

Game-theory core: WE play optimally; the OPPONENT's nodes are blended between their
optimal reply (pure minimax, `pessimism = 1` → unexploitable, safe) and the average
over their legal moves (`pessimism = 0` → expectimax that exploits a sub-optimal
opponent). The Cop's action set includes walling an adjacent cell (the Conway 'Devil'
move), so the planner discovers herding-to-trap lines without a hand-coded rule.
"""

from __future__ import annotations

from cop_thief.domain.constants import ActionType, AgentRole
from cop_thief.domain.state import DecPomdpGameState
from cop_thief.domain.strategy.evaluation import Evaluator

Action = tuple[ActionType, tuple]


class MinimaxPlanner:
    """Risk-tunable planner returning the acting role's chosen action."""

    def __init__(self, evaluator: Evaluator | None = None, depth: int = 3,
                 pessimism: float = 1.0, barriers: bool = True) -> None:
        """Bind the leaf evaluator, search depth, default opponent pessimism, and barrier toggle."""
        self._eval = evaluator or Evaluator()
        self._depth = depth
        self._pessimism = pessimism
        self._barriers = barriers

    def actions(self, state: DecPomdpGameState, role: AgentRole) -> list[Action]:
        """Enumerate legal actions: King moves, plus Cop barriers (wall an adjacent free cell)."""
        steps = state.legal_moves(role)
        acts: list[Action] = [(ActionType.MOVE, cell) for cell in steps]
        if self._barriers and role is AgentRole.COP and state.cop_barriers_left > 0:
            acts += [(ActionType.PLACE_BARRIER, cell) for cell in steps if state.is_barrier_legal(cell)]
        if not acts:  # boxed in — HOLD in place (terminal scoring resolves the loss)
            pos = state.cop_pos if role is AgentRole.COP else state.thief_pos
            acts.append((ActionType.MOVE, pos))
        return acts

    def _search(self, state: DecPomdpGameState, depth: int, our_role: AgentRole, pess: float) -> float:
        terminal = self._eval.terminal_value(state)
        if terminal is not None:
            return terminal
        if depth == 0:
            return self._eval.value(state)
        role = state.turn_role
        scores = [
            self._search(state.apply_action(role, at, tgt), depth - 1, our_role, pess)
            for at, tgt in self.actions(state, role)
        ]
        if role is our_role:  # we always play optimally
            return max(scores) if role is AgentRole.COP else min(scores)
        optimal = min(scores) if role is AgentRole.THIEF else max(scores)  # opponent's best reply
        return pess * optimal + (1.0 - pess) * (sum(scores) / len(scores))

    def best_action(self, state: DecPomdpGameState, pessimism: float | None = None) -> Action:
        """Return the (ActionType, target) the acting role should play now."""
        pess = self._pessimism if pessimism is None else pessimism
        role = state.turn_role
        scored = [
            (self._search(state.apply_action(role, at, tgt), self._depth - 1, role, pess), (at, tgt))
            for at, tgt in self.actions(state, role)
        ]
        chooser = max if role is AgentRole.COP else min
        return chooser(scored, key=lambda pair: pair[0])[1]
