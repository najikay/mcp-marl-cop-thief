"""Depth-limited alpha-beta minimax over the zero-sum Markov game.

Game-theory core: the Cop maximizes and the Thief minimizes the cop-signed value,
each assuming an optimal adversary. The Cop's action set includes walling its own
cell (the Conway 'Devil' move), so the planner discovers herding-to-trap lines
without any hand-coded barrier heuristic.
"""

from __future__ import annotations

import math

from cop_thief.domain.constants import ActionType, AgentRole
from cop_thief.domain.state import DecPomdpGameState
from cop_thief.domain.strategy.evaluation import Evaluator

Action = tuple[ActionType, tuple]


class MinimaxPlanner:
    """Alpha-beta planner returning the acting role's optimal action."""

    def __init__(self, evaluator: Evaluator | None = None, depth: int = 3) -> None:
        """Bind the leaf evaluator and the search depth (plies)."""
        self._eval = evaluator or Evaluator()
        self._depth = depth

    def actions(self, state: DecPomdpGameState, role: AgentRole) -> list[Action]:
        """Enumerate legal actions: King moves, plus a Cop wall on its own cell."""
        acts: list[Action] = [(ActionType.MOVE, cell) for cell in state.legal_moves(role)]
        if (role is AgentRole.COP and state.cop_barriers_left > 0
                and state.is_barrier_legal(state.cop_pos)):
            acts.append((ActionType.PLACE_BARRIER, state.cop_pos))
        if not acts:  # boxed in — HOLD in place (terminal scoring resolves the loss)
            pos = state.cop_pos if role is AgentRole.COP else state.thief_pos
            acts.append((ActionType.MOVE, pos))
        return acts

    def _search(self, state: DecPomdpGameState, depth: int, alpha: float, beta: float) -> float:
        terminal = self._eval.terminal_value(state)
        if terminal is not None:
            return terminal
        if depth == 0:
            return self._eval.value(state)
        role = state.turn_role
        maximizing = role is AgentRole.COP
        best = -math.inf if maximizing else math.inf
        for action_type, target in self.actions(state, role):
            score = self._search(state.apply_action(role, action_type, target), depth - 1, alpha, beta)
            if maximizing:
                best = max(best, score)
                alpha = max(alpha, best)
            else:
                best = min(best, score)
                beta = min(beta, best)
            if beta <= alpha:
                break
        return best

    def best_action(self, state: DecPomdpGameState) -> Action:
        """Return the (ActionType, target) the acting role should play now."""
        role = state.turn_role
        scored = [
            (self._search(state.apply_action(role, at, tgt), self._depth - 1, -math.inf, math.inf), (at, tgt))
            for at, tgt in self.actions(state, role)
        ]
        chooser = max if role is AgentRole.COP else min
        return chooser(scored, key=lambda pair: pair[0])[1]
