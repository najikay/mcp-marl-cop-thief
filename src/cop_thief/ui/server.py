"""One-way Server-Sent-Events broadcast server (the 'Dumb Television' backend).

Serves a single static HTML canvas and a ``text/event-stream`` of immutable turn
snapshots. The UI is broadcast-only: it can never mutate Python game state.

Standalone for now (not wired into main.py): ``/stream`` is fed by a sterile
``mock_game_generator`` so the browser can be tested without a live game.
"""

from __future__ import annotations

import asyncio
import json
from pathlib import Path

from starlette.applications import Starlette
from starlette.responses import FileResponse, StreamingResponse
from starlette.routing import Route

_STATIC = Path(__file__).parent / "static" / "index.html"
_GRID = 5
_TOTAL = 10
_DELAY_S = 1.5

# Sterile 5-turn capture sequence (cop closes the diagonal; collision on turn 5).
_SEQUENCE = [
    {"turn": 1, "cop": [1, 1], "thief": [3, 4], "captured": False, "epistemic": "Conway Scaffolding", "cost_usd": 0.0004, "cop_prose": "I press in from the damp north-west cobblestones.", "thief_prose": "I drift along the eastern wall, watching the lanes."},
    {"turn": 2, "cop": [2, 2], "thief": [4, 4], "captured": False, "epistemic": "Q-Policy", "cost_usd": 0.0009, "cop_prose": "Closing the diagonal — your corner is shrinking.", "thief_prose": "I hug the far corner; you are still two strides away."},
    {"turn": 3, "cop": [2, 3], "thief": [3, 4], "captured": False, "epistemic": "Q-Policy", "cost_usd": 0.0013, "cop_prose": "I slide east to seal your escape north.", "thief_prose": "Edging up the wall, but the gap is thinning."},
    {"turn": 4, "cop": [3, 3], "thief": [4, 4], "captured": False, "epistemic": "Q-Policy", "cost_usd": 0.0018, "cop_prose": "One lane left. I drop south-east onto your shadow.", "thief_prose": "Cornered against the eastern rampart — running out of board."},
    {"turn": 5, "cop": [3, 4], "thief": [3, 4], "captured": True, "epistemic": "Q-Policy", "cost_usd": 0.0022, "cop_prose": "Got you. Same cell — capture.", "thief_prose": "Trapped. The lanes are gone."},
]


async def mock_game_generator():
    """Yield a sterile 5-turn capture sequence, one packet per delay tick."""
    for packet in _SEQUENCE:
        yield {"grid": _GRID, "total": _TOTAL, **packet}
        await asyncio.sleep(_DELAY_S)


async def homepage(_request) -> FileResponse:
    """Serve the single-file HTML television."""
    return FileResponse(_STATIC)


async def stream(_request) -> StreamingResponse:
    """Stream turn snapshots as Server-Sent Events (one-way broadcast)."""
    async def event_source():
        async for packet in mock_game_generator():
            yield f"data: {json.dumps(packet)}\n\n"

    return StreamingResponse(event_source(), media_type="text/event-stream")


app = Starlette(routes=[Route("/", homepage), Route("/stream", stream)])


def main() -> None:
    """Run the broadcast server on localhost:8800."""
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8800)


if __name__ == "__main__":
    main()
