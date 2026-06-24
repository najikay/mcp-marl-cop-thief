"""TDD unit tests for the SSE broadcast bus (feed / observe / subscribe)."""

from __future__ import annotations

import asyncio
import json

from cop_thief.domain.state import DecPomdpGameState
from cop_thief.ui import broadcast


def _drain() -> None:
    while not broadcast._QUEUE.empty():
        broadcast._QUEUE.get_nowait()


def _next_payload() -> dict:
    chunk = asyncio.run(broadcast.subscribe().__anext__())
    assert chunk.startswith("data: ") and chunk.endswith("\n\n")
    return json.loads(chunk[len("data: "):].strip())


def test_feed_then_subscribe_formats_sse_string() -> None:
    """feed() enqueues a packet; subscribe() yields a formatted SSE JSON string."""
    _drain()
    broadcast.feed({"turn": 3, "cop": [1, 1]}, "cop says", "", "live")
    payload = _next_payload()
    assert payload["turn"] == 3
    assert payload["cop_prose"] == "cop says"
    assert payload["thief_prose"] == ""
    assert payload["status"] == "live"


def test_observe_builds_packet_from_state() -> None:
    """observe() derives barriers/epistemic/status from a live game state."""
    _drain()
    state = DecPomdpGameState(cop_pos=(2, 2), thief_pos=(2, 2))
    broadcast.observe(state, "got you", informed=True)
    payload = _next_payload()
    assert payload["captured"] is True and payload["status"] == "capture"
    assert payload["epistemic"] == "Q-Policy"
    assert payload["barriers"] == []
