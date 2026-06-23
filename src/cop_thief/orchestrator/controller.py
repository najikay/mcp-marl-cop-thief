"""Game loop controller: coordinates the turn-taking tick across the network.

Ties encoder -> firewall -> parser -> SDK into one cycle. Our own moves delegate
to the tabular Q-learning strategy (Tier-1) and learn online; when the Q-row is
uninformed it falls back to Conway-aware geometry (Tier-2). Opponent moves are
advanced via the immutable geometry executor.
"""

from __future__ import annotations

from cop_thief.config import get_config_manager
from cop_thief.domain.constants import ActionType, AgentRole, SubGameOutcome
from cop_thief.domain.geometry import (
    calculate_manhattan,
    get_adjacent_coords,
    is_conway_trap_inevitable,
)
from cop_thief.domain.grid import Grid
from cop_thief.domain.state import DecPomdpGameState
from cop_thief.domain.strategy import QTableStrategy
from cop_thief.orchestrator.encoder import NaturalLanguageEncoder
from cop_thief.orchestrator.firewall import CognitiveFirewall
from cop_thief.orchestrator.parser import DefensiveNlParser
from cop_thief.sdk import CopThiefSDK

_STANDARD = "STANDARD"


def _opponent(role: AgentRole) -> AgentRole:
    """Return the opposing role."""
    return AgentRole.THIEF if role is AgentRole.COP else AgentRole.COP


class GameLoopController:
    """Drive a single turn cycle and autonomous sub-game simulation."""

    def __init__(self, sdk=None, encoder=None, parser=None, firewall=None, strategy=None) -> None:
        """Wire the SDK, encoder, parser, firewall and Q-learning strategy."""
        self._sdk = sdk or CopThiefSDK()
        self._encoder = encoder or NaturalLanguageEncoder()
        self._parser = parser or DefensiveNlParser()
        self._firewall = firewall or CognitiveFirewall()
        self._strategy = strategy or QTableStrategy()
        self._rewards = get_config_manager().get_setup().rl.rewards

    def _geometry_target(self, state: DecPomdpGameState, role: AgentRole) -> tuple:
        """Tier-2 fallback: cop pursues (Conway-aware), thief flees."""
        pos = state.cop_pos if role is AgentRole.COP else state.thief_pos
        ref = state.thief_pos if role is AgentRole.COP else state.cop_pos
        legal = [c for c in get_adjacent_coords(pos, state.grid.shape) if state.grid.is_legal_move(pos, c)]
        if not legal:
            return pos
        if role is AgentRole.COP:
            barriers = set(state.grid.barriers)
            traps = [c for c in legal if is_conway_trap_inevitable(c, ref, barriers, state.grid.shape)]
            pool = traps or legal
            return min(pool, key=lambda c: calculate_manhattan(c, ref))
        return max(legal, key=lambda c: calculate_manhattan(c, ref))

    def _reward(self, state: DecPomdpGameState, role: AgentRole) -> tuple[float, bool]:
        """Compute the RL reward + terminal flag from the resulting state."""
        rw = self._rewards
        if state.cop_pos == state.thief_pos:
            return (rw.r_capture if role is AgentRole.COP else rw.r_caught, True)
        if state.turn_counter >= self._sdk.max_moves:
            return (rw.r_evasion if role is AgentRole.THIEF else rw.r_step, True)
        return (rw.r_step, False)

    def execute_single_turn_cycle(
        self,
        state: DecPomdpGameState,
        rival_group_id: str,
        inbound_opponent_prose: str | None = None,
    ) -> tuple[DecPomdpGameState, str]:
        """Run one tick: grudge intercept, then our move or opponent ingest."""
        our_role = self._sdk.current_role
        posture = self._firewall.get_outgoing_posture(our_role, rival_group_id)
        if posture != _STANDARD:  # STEP A: grudge intercept
            return state, posture
        if state.turn_role is our_role:  # STEP B: our turn (learned policy)
            observation = state.get_subjective_observation(our_role)
            prose = self._encoder.generate_prose_transmission(state, our_role, observation)
            target = self._strategy.select_target(state, our_role, fallback=self._geometry_target)
            new_state = self._sdk.process_turn(state, ActionType.MOVE, target)
            reward, done = self._reward(new_state, our_role)
            self._strategy.observe(reward, new_state, done)
            return new_state, prose
        opponent = _opponent(our_role)  # STEP C: their turn
        safe, _payload = self._firewall.filter_inbound(
            inbound_opponent_prose or "", opponent, rival_group_id
        )
        if not safe:
            return state, self._firewall.get_outgoing_posture(our_role, rival_group_id)
        self._parser.parse_inbound_prose(inbound_opponent_prose or "", opponent)
        target = self._geometry_target(state, opponent)
        return state.apply_action(opponent, ActionType.MOVE, target), "acknowledged"

    def run_simulated_sub_game(self, rival_group_id: str = "mock_partner_node") -> SubGameOutcome:
        """Autonomously tick a full sub-game to its terminal outcome."""
        self._sdk.initialize_match()
        rows, cols = self._sdk.grid_shape
        state = DecPomdpGameState(
            cop_pos=(0, 0), thief_pos=(rows - 1, cols - 1), grid=Grid(shape=(rows, cols))
        )
        for _ in range(self._sdk.max_moves * 2):
            outcome = self._sdk.evaluate_terminal(state)
            if outcome is not None:
                self._strategy.decay_epsilon()
                return outcome
            state, _ = self.execute_single_turn_cycle(
                state, rival_group_id, inbound_opponent_prose="I edge along the wall."
            )
        return self._sdk.evaluate_terminal(state) or SubGameOutcome.THIEF_WINS
