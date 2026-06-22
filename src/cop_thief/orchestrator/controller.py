"""Game loop controller: coordinates the turn-taking tick across the network.

Ties encoder -> firewall -> parser -> SDK into one cycle. Move selection here is
a deterministic geometric placeholder (cop minimises, thief maximises distance);
the Phase-7.D/E strategy engine will supersede it. Opponent advancement uses the
immutable ``state.apply_action`` executor that the SDK itself delegates to.
"""

from __future__ import annotations

from cop_thief.domain.constants import ActionType, AgentRole, SubGameOutcome
from cop_thief.domain.geometry import calculate_manhattan, get_adjacent_coords
from cop_thief.domain.grid import Grid
from cop_thief.domain.state import DecPomdpGameState
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

    def __init__(self, sdk=None, encoder=None, parser=None, firewall=None) -> None:
        """Wire the SDK, encoder, parser and cognitive firewall (injectable)."""
        self._sdk = sdk or CopThiefSDK()
        self._encoder = encoder or NaturalLanguageEncoder()
        self._parser = parser or DefensiveNlParser()
        self._firewall = firewall or CognitiveFirewall()

    def _choose_target(self, state: DecPomdpGameState, role: AgentRole) -> tuple:
        """Pick a deterministic legal step (cop pursues, thief flees)."""
        pos = state.cop_pos if role is AgentRole.COP else state.thief_pos
        ref = state.thief_pos if role is AgentRole.COP else state.cop_pos
        legal = [
            cell
            for cell in get_adjacent_coords(pos, state.grid.shape)
            if state.grid.is_legal_move(pos, cell)
        ]
        if not legal:
            return pos
        if role is AgentRole.COP:
            return min(legal, key=lambda c: calculate_manhattan(c, ref))
        return max(legal, key=lambda c: calculate_manhattan(c, ref))

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
        if state.turn_role is our_role:  # STEP B: our turn
            observation = state.get_subjective_observation(our_role)
            prose = self._encoder.generate_prose_transmission(state, our_role, observation)
            target = self._choose_target(state, our_role)
            return self._sdk.process_turn(state, ActionType.MOVE, target), prose
        opponent = _opponent(our_role)  # STEP C: their turn
        safe, _payload = self._firewall.filter_inbound(
            inbound_opponent_prose or "", opponent, rival_group_id
        )
        if not safe:
            return state, self._firewall.get_outgoing_posture(our_role, rival_group_id)
        self._parser.parse_inbound_prose(inbound_opponent_prose or "", opponent)
        target = self._choose_target(state, opponent)
        return state.apply_action(opponent, ActionType.MOVE, target), "acknowledged"

    def run_simulated_sub_game(
        self, rival_group_id: str = "mock_partner_node"
    ) -> SubGameOutcome:
        """Autonomously tick a full sub-game to its terminal outcome."""
        self._sdk.initialize_match()
        rows, cols = self._sdk.grid_shape
        state = DecPomdpGameState(
            cop_pos=(0, 0), thief_pos=(rows - 1, cols - 1), grid=Grid(shape=(rows, cols))
        )
        for _ in range(self._sdk.max_moves * 2):
            outcome = self._sdk.evaluate_terminal(state)
            if outcome is not None:
                return outcome
            state, _ = self.execute_single_turn_cycle(
                state, rival_group_id, inbound_opponent_prose="I edge along the wall."
            )
        return self._sdk.evaluate_terminal(state) or SubGameOutcome.THIEF_WINS
