"""Concurrent dual FastMCP host: Cop (:8001) and Thief (:8002) over MCP streamable-HTTP.

Wraps the existing Cop/Thief FastMCP servers (with their tool layers) as Starlette
ASGI apps via FastMCP's streamable-HTTP transport (tool endpoint at ``/mcp``), then
runs both under one asyncio event loop with two programmatic Uvicorn servers. These
are the local targets behind the Cloudflare tunnels (8001 → Cop, 8002 → Thief); the
shared public URLs are ``https://…trycloudflare.com/mcp/`` (matches the standard).

Run: ``uv run python -m cop_thief.infra.network.dual_mcp_host``
"""

from __future__ import annotations

import asyncio

import uvicorn

from cop_thief.servers import create_cop_server, create_thief_server
from cop_thief.servers.inbound_observer import OBSERVER

_HOST = "127.0.0.1"
_COP_PORT = 8001
_THIEF_PORT = 8002
_LOG_LEVEL = "warning"


def build_servers() -> tuple[uvicorn.Server, uvicorn.Server]:
    """Build two configured (not-yet-serving) Uvicorn servers for Cop/Thief.

    Each FastMCP instance is converted to an ASGI app via ``http_app(transport=
    "http")`` (streamable-HTTP, endpoint ``/mcp``) and bound to its localhost port.
    """
    cop_app = create_cop_server(observer=OBSERVER).http_app(transport="http")
    thief_app = create_thief_server(observer=OBSERVER).http_app(transport="http")
    cop = uvicorn.Server(
        uvicorn.Config(cop_app, host=_HOST, port=_COP_PORT, log_level=_LOG_LEVEL)
    )
    thief = uvicorn.Server(
        uvicorn.Config(thief_app, host=_HOST, port=_THIEF_PORT, log_level=_LOG_LEVEL)
    )
    return cop, thief


def _print_banner() -> None:
    """Print a scannable startup banner for both listening ASGI loops."""
    rows = [
        "DUAL MCP HOST — MCP-over-SSE ASGI layers LISTENING",
        f"Cop   MCP  >  http://{_HOST}:{_COP_PORT}   (SSE transport)",
        f"Thief MCP  >  http://{_HOST}:{_THIEF_PORT}   (SSE transport)",
    ]
    width = max(len(row) for row in rows) + 2
    bar = "═" * width
    print(f"╔{bar}╗")
    for row in rows:
        print(f"║ {row.ljust(width - 1)}║")
    print(f"╚{bar}╝")


async def run_hosts() -> None:
    """Serve both MCP ASGI apps concurrently in one event loop."""
    cop, thief = build_servers()
    _print_banner()
    await asyncio.gather(cop.serve(), thief.serve())


def main() -> None:
    """Run the dual MCP host until interrupted."""
    try:
        asyncio.run(run_hosts())
    except KeyboardInterrupt:
        print("\nDual MCP host shut down; both ASGI loops closed.")


if __name__ == "__main__":
    main()
