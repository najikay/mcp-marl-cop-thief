"""Natural-language encoder: board state -> qualitative, non-numeric prose."""

from __future__ import annotations

from cop_thief.domain.agent import harden
from cop_thief.domain.constants import AgentRole
from cop_thief.domain.state import DecPomdpGameState
from cop_thief.infra.gatekeeper import ApiGatekeeper, build_default_gatekeeper
from cop_thief.orchestrator.exceptions import NaturalLanguageTranslationError

_ENCODER_SYSTEM = (
    "You are an autonomous agent in a grid pursuit game. Translate your private "
    "position into rich, atmospheric, QUALITATIVE prose describing where you are "
    "and your intent (e.g. 'I have advanced into the damp cobblestones of the "
    "northeast sector, setting up a perimeter'). ABSOLUTELY FORBIDDEN: raw "
    "coordinates, digits, grid indices like (2,3), or any numerals. Speak only in "
    "natural human language using compass sectors, walls and terrain. One or two "
    "sentences."
)


class NaturalLanguageEncoder:
    """Encode a player's state into opponent-facing natural-language prose."""

    def __init__(self, gatekeeper: ApiGatekeeper | None = None) -> None:
        """Use an injected gatekeeper, or build the default from config."""
        self._gatekeeper = gatekeeper or build_default_gatekeeper()

    @staticmethod
    def _build_user_prompt(role: AgentRole, observation: dict) -> str:
        """Compose the user prompt from the agent's subjective observation."""
        sector = observation.get("opponent_sector") or "an unknown bearing"
        visible = observation.get("opponent_visible")
        return (
            f"You play the {role.value}. Your own cell is {observation.get('self_pos')}. "
            f"Opponent visible: {visible}; opponent appears toward {sector}. "
            "Compose your message to the opponent now (qualitative prose only)."
        )

    def generate_prose_transmission(
        self, state: DecPomdpGameState, role: AgentRole, observation: dict
    ) -> str:
        """Translate the agent's state into non-numeric prose via the gatekeeper.

        Raises ``NaturalLanguageTranslationError`` on empty LLM output.
        """
        _ = state
        prompt = self._build_user_prompt(role, observation)
        text, _usage = self._gatekeeper.execute_llm_call(prompt, harden(_ENCODER_SYSTEM))
        if not text or not text.strip():
            raise NaturalLanguageTranslationError("LLM returned empty prose.")
        return text
