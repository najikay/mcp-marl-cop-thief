"""Live broadcast bus bridging the game loop to the SSE television.

``feed`` is the canonical non-blocking push (called with a pre-built state dict);
``observe`` is the GameLoopController hook that derives the dict from a live
state; ``subscribe`` yields ready-to-emit Server-Sent-Event strings.
"""

from __future__ import annotations

import asyncio
import contextlib
import json

_QUEUE: asyncio.Queue = asyncio.Queue(maxsize=512)
_TOTAL = 25


def feed(state_dict: dict, cop_prose: str, thief_prose: str, status: str) -> None:
    """Non-blocking observer push: enqueue one live turn packet (drop if full)."""
    packet = {**state_dict, "cop_prose": cop_prose, "thief_prose": thief_prose, "status": status}
    with contextlib.suppress(asyncio.QueueFull):
        _QUEUE.put_nowait(packet)


def observe(state, prose: str, informed: bool) -> None:
    """GameLoopController hook: derive a packet from ``state`` and feed the bus."""
    actor = "thief" if state.turn_role.value == "cop" else "cop"
    captured = state.cop_pos == state.thief_pos
    state_dict = {
        "grid": state.grid.shape[0],
        "total": _TOTAL,
        "turn": state.turn_counter,
        "cop": list(state.cop_pos),
        "thief": list(state.thief_pos),
        "barriers": [list(cell) for cell in state.grid.barriers],
        "captured": captured,
        "epistemic": "Q-Policy" if informed else "Conway Scaffolding",
        "cost_usd": 0.0,
    }
    feed(
        state_dict,
        prose if actor == "cop" else "",
        prose if actor == "thief" else "",
        "capture" if captured else "live",
    )


def banner(label: str) -> None:
    """Push a UI separator (new match/game divider) onto the bus."""
    feed({"separator": label}, "", "", "info")


async def subscribe():
    """Yield formatted Server-Sent-Event JSON strings for the /stream endpoint."""
    while True:
        packet = await _QUEUE.get()
        yield f"data: {json.dumps(packet)}\n\n"
