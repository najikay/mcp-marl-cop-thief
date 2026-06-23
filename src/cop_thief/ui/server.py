"""SSE web server — stream live games to a browser canvas.

Reuses the Starlette/uvicorn/sse-starlette stack already pulled in by FastMCP, so
no extra dependency. ``/`` serves the page; ``/events`` streams an endless run of
sub-games as JSON Server-Sent Events. ``build_app`` is unit-testable; the
endpoints and ``main`` (network/streaming) are excluded from coverage.
"""

from __future__ import annotations

import asyncio
import json
from pathlib import Path

from sse_starlette.sse import EventSourceResponse
from starlette.applications import Starlette
from starlette.responses import FileResponse
from starlette.routing import Route

from ..sdk import CopThiefSDK

_STATIC = Path(__file__).parent / "static"
_FRAME_DELAY = 0.4
_GAME_PAUSE = 1.4


def _index(_request):  # pragma: no cover - serves a static file
    return FileResponse(_STATIC / "index.html")


async def _events(_request):  # pragma: no cover - infinite SSE stream
    sdk = CopThiefSDK()
    rows, cols = sdk.config.grid_size

    async def stream():
        yield {"data": json.dumps({"type": "config", "rows": rows, "cols": cols})}
        cop_wins = thief_wins = 0
        while True:
            frames = sdk.record_sub_game()
            for frame in frames:
                yield {"data": json.dumps({"type": "frame", **frame})}
                await asyncio.sleep(_FRAME_DELAY)
            captured = frames[-1]["cop"] == frames[-1]["thief"]
            cop_wins += int(captured)
            thief_wins += int(not captured)
            outcome = {
                "type": "outcome",
                "captured": captured,
                "cop_wins": cop_wins,
                "thief_wins": thief_wins,
            }
            yield {"data": json.dumps(outcome)}
            await asyncio.sleep(_GAME_PAUSE)

    return EventSourceResponse(stream())


def build_app() -> Starlette:
    """Construct the Starlette app (routes for the page and the SSE stream)."""
    return Starlette(routes=[Route("/", _index), Route("/events", _events)])


def main() -> None:  # pragma: no cover - launches a blocking server
    """Console entrypoint: serve the live view on http://127.0.0.1:8080."""
    import uvicorn

    uvicorn.run(build_app(), host="127.0.0.1", port=8080)
