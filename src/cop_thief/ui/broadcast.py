"""Live broadcast bus bridging the game loop to the SSE television.

The game-loop calls :func:`feed` (a one-way observer hook); the SSE ``/stream``
endpoint consumes :func:`subscribe`. The UI remains a strict receiver.
"""

from __future__ import annotations

import asyncio
import contextlib

from cop_thief.domain.constants import AgentRole

_QUEUE: asyncio.Queue = asyncio.Queue(maxsize=512)
_GRID = 5
_TOTAL = 25


def make_packet(state, prose: str, informed: bool) -> dict:
    """Build an immutable SSE snapshot from a game state + the turn's prose."""
    actor = "thief" if state.turn_role.value == "cop" else "cop"
    captured = state.cop_pos == state.thief_pos
    trapped = not state.legal_moves(AgentRole.THIEF)
    status = "capture" if captured else "thief_trapped" if trapped else "live"
    return {
        "grid": _GRID,
        "total": _TOTAL,
        "turn": state.turn_counter,
        "cop": list(state.cop_pos),
        "thief": list(state.thief_pos),
        "barriers": [list(cell) for cell in state.grid.barriers],
        "captured": captured,
        "status": status,
        "epistemic": "Q-Policy" if informed else "Conway Scaffolding",
        "cost_usd": 0.0,
        "cop_prose": prose if actor == "cop" else "",
        "thief_prose": prose if actor == "thief" else "",
    }


def feed(state, prose: str, informed: bool) -> None:
    """Game-loop observer hook: enqueue a live snapshot (drop if the bus is full)."""
    with contextlib.suppress(asyncio.QueueFull):
        _QUEUE.put_nowait(make_packet(state, prose, informed))


async def subscribe():
    """Async generator yielding live packets for the SSE stream."""
    while True:
        yield await _QUEUE.get()
