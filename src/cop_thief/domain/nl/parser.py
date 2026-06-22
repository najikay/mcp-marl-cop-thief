"""NLParser — recover a :class:`BeliefUpdate` from an opponent's free text.

If an LLM is supplied it is asked (through the gatekeeper) to extract structured
JSON; any failure falls back to a deterministic keyword heuristic. With no LLM
the heuristic runs alone, so the whole pipeline works offline. The parser is
defensive: when nothing parses it returns a zero-confidence default, never an
exception (PLAN §4.3).
"""

from __future__ import annotations

import json

from ...constants import Direction
from .belief import COL_SYNONYMS, DIRECTION_PHRASES, ROW_SYNONYMS, BeliefUpdate

_PROMPT = (
    "Extract the opponent's location cues from this message and reply with JSON "
    '{{"region_row": "north|central|south|null", "region_col": "west|central|east|null", '
    '"barrier_mentioned": true|false, "confidence": 0..1}}.\nMessage: {text}'
)


def _detect(text: str, synonyms: dict[str, tuple[str, ...]]) -> str | None:
    """Return the first band whose any synonym appears in ``text``."""
    for band, words in synonyms.items():
        if any(word in text for word in words):
            return band
    return None


def _detect_direction(text: str) -> Direction | None:
    """Find a movement direction phrase (compound phrases checked first)."""
    for direction in DIRECTION_PHRASES:
        if direction is Direction.STAY:
            continue
        if DIRECTION_PHRASES[direction] in text:
            return direction
    return None


class NLParser:
    """Parse natural-language messages into actionable beliefs."""

    def __init__(self, llm=None, gatekeeper=None) -> None:
        self._llm = llm
        self._gatekeeper = gatekeeper

    def parse(self, text: str) -> BeliefUpdate:
        """Parse ``text`` via the LLM if available, else the heuristic."""
        if self._llm is not None:
            belief = self._parse_via_llm(text)
            if belief is not None:
                return belief
        return self._parse_heuristic(text)

    def _parse_heuristic(self, text: str) -> BeliefUpdate:
        low = text.lower()
        row = _detect(low, ROW_SYNONYMS)
        col = _detect(low, COL_SYNONYMS)
        moved = _detect_direction(low)
        barrier = any(word in low for word in ("barrier", "wall", "seal", "sealed"))
        cues = sum(x is not None for x in (row, col, moved)) + (1 if barrier else 0)
        if cues == 0:
            return BeliefUpdate.unknown()
        return BeliefUpdate(row, col, moved, barrier, min(1.0, cues / 3))

    def _parse_via_llm(self, text: str) -> BeliefUpdate | None:
        try:
            raw = self._call(_PROMPT.format(text=text))
            data = json.loads(raw)
            return BeliefUpdate(
                region_row=data.get("region_row") or None,
                region_col=data.get("region_col") or None,
                moved=None,
                barrier_mentioned=bool(data.get("barrier_mentioned", False)),
                confidence=float(data.get("confidence", 0.5)),
            )
        except (ValueError, TypeError, KeyError, json.JSONDecodeError):
            return None

    def _call(self, prompt: str) -> str:
        if self._gatekeeper is not None:
            return self._gatekeeper.execute("llm", lambda: self._llm.complete(prompt))
        return self._llm.complete(prompt)
