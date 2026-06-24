"""Deterministic move language: the treaty `[INTENT]` + direction-word contract.

Both peers encode/parse moves identically (no LLM needed for resolution), so two
machines stay in lock-step. Longer direction words are matched first so that
"north-east" is never mis-read as "north".
"""

from __future__ import annotations

from cop_thief.domain.constants import ActionType, AgentRole

_WORD = {
    (-1, 0): "north", (1, 0): "south", (0, 1): "east", (0, -1): "west",
    (-1, 1): "north-east", (-1, -1): "north-west", (1, 1): "south-east",
    (1, -1): "south-west", (0, 0): "hold",
}
_DELTA = {word: delta for delta, word in _WORD.items()}
_BY_LEN = sorted(_DELTA, key=len, reverse=True)


def encode_move(role: AgentRole, before: tuple, after: tuple) -> str:
    """Render a move as treaty prose, e.g. ``[INTENT: MOVE] The thief edges north-east.``"""
    word = _WORD.get((after[0] - before[0], after[1] - before[1]), "hold")
    intent = "HOLD" if word == "hold" else "MOVE"
    return f"[INTENT: {intent}] The {role.value} edges {word}."


def encode_barrier(role: AgentRole, before: tuple, target: tuple) -> str:
    """Render a barrier placement, e.g. ``[INTENT: BARRIER] The cop seals the cell north.``"""
    word = _WORD.get((target[0] - before[0], target[1] - before[1]), "hold")
    return f"[INTENT: BARRIER] The {role.value} seals the cell {word}."


def parse_target(prose: str, pos: tuple) -> tuple:
    """Resolve the target cell from prose (longest direction word wins; default STAY)."""
    lowered = prose.lower()
    for word in _BY_LEN:
        if word in lowered:
            delta = _DELTA[word]
            return (pos[0] + delta[0], pos[1] + delta[1])
    return pos


def parse_intent(prose: str) -> str:
    """Return the declared ``[INTENT: …]`` token (BARRIER / HOLD / MOVE).

    Only the bracketed prefix is read, so opponent flavor text cannot spoof intent.
    """
    head = prose.split("]", 1)[0].lower()
    if "barrier" in head:
        return "BARRIER"
    if "hold" in head:
        return "HOLD"
    return "MOVE"


def apply_prose(state, role: AgentRole, prose: str):
    """Apply a peer's prose move to ``state`` (illegal/unparsable → HOLD in place).

    A ``[INTENT: BARRIER]`` declaration seals the named adjacent cell (validated by
    the Adjacent Barrier Law; an illegal seal is a no-op turn). Otherwise it is a MOVE.
    """
    pos = state.cop_pos if role is AgentRole.COP else state.thief_pos
    target = parse_target(prose, pos)
    if parse_intent(prose) == "BARRIER":
        return state.apply_action(role, ActionType.PLACE_BARRIER, target)
    if not state.grid.is_legal_move(pos, target):
        target = pos
    return state.apply_action(role, ActionType.MOVE, target)
