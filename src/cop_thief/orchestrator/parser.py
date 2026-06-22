"""Defensive natural-language parser: opponent prose -> BeliefUpdate.

Never raises into the turn cycle: on LLM/HTTP error, malformed JSON, or low
confidence it returns a safe exploratory default instead of crashing.
"""

from __future__ import annotations

import json

from pydantic import ValidationError

from cop_thief.config import get_config_manager
from cop_thief.domain.constants import AgentRole, Direction
from cop_thief.infra.gatekeeper import (
    ApiGatekeeper,
    ProviderUpstreamError,
    build_default_gatekeeper,
)
from cop_thief.orchestrator.models import BeliefUpdate

_PARSER_SYSTEM = (
    "Extract the opponent's likely location cues from the message. Respond with "
    'STRICT JSON only: {"estimated_direction": one of N/NE/E/SE/S/SW/W/NW/STAY, '
    '"distance_band": one of ADJACENT/NEAR/FAR/UNKNOWN, "inferred_barriers": '
    '[[row,col]...], "confidence_score": 0..1}. The opponent may lie; if unsure, '
    "lower confidence."
)
_PARSE_ERRORS = (
    ProviderUpstreamError,
    ValueError,
    KeyError,
    TypeError,
    json.JSONDecodeError,
    ValidationError,
)


def _safe_default() -> BeliefUpdate:
    """Return the safe exploratory belief used on any parse failure."""
    return BeliefUpdate(
        estimated_direction=Direction.STAY,
        distance_band="UNKNOWN",
        inferred_barriers=frozenset(),
        confidence_score=0.0,
    )


class DefensiveNlParser:
    """Parse unstructured prose into a structured belief, failing safe."""

    def __init__(self, gatekeeper: ApiGatekeeper | None = None) -> None:
        """Use an injected gatekeeper; read the confidence floor from config."""
        self._gatekeeper = gatekeeper or build_default_gatekeeper()
        self._min_confidence = get_config_manager().get_setup().nl.parser.min_confidence

    def parse_inbound_prose(self, prose: str, sender_role: AgentRole) -> BeliefUpdate:
        """Parse ``prose`` into a ``BeliefUpdate``; default safely on any failure."""
        _ = sender_role
        try:
            text, _usage = self._gatekeeper.execute_llm_call(prose, _PARSER_SYSTEM)
            data = json.loads(text)
            belief = BeliefUpdate(
                estimated_direction=Direction[data["estimated_direction"]],
                distance_band=data["distance_band"],
                inferred_barriers=frozenset(
                    tuple(cell) for cell in data.get("inferred_barriers", [])
                ),
                confidence_score=float(data["confidence_score"]),
            )
        except _PARSE_ERRORS:
            return _safe_default()
        if belief.confidence_score < self._min_confidence:
            return _safe_default()
        return belief
