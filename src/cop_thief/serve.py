"""One-command public node: serve both MCP servers AND open their tunnels together.

Collapses the two hosting terminals into one so the Cloudflare tunnels can never
point at a dead origin (the cause of HTTP 530s). It serves Cop ``:8001/mcp`` +
Thief ``:8002/mcp`` and runs the cloudflared switchboard in the **same** event
loop, then prints the shareable ``…/mcp/`` URLs and holds open until Ctrl+C.

Run: ``uv run python -m cop_thief.serve`` — then share the printed URLs + tokens.
"""

from __future__ import annotations

import asyncio

from cop_thief.infra.network.dual_mcp_host import build_servers
from cop_thief.infra.network.switchboard import run_switchboard


async def run_node() -> None:
    """Serve both MCP servers and run the tunnels concurrently in one event loop."""
    cop, thief = build_servers()
    print("Booting MCP servers (:8001/mcp, :8002/mcp) + tunnels — URLs appear below ...")
    await asyncio.gather(cop.serve(), thief.serve(), run_switchboard())


def main() -> None:
    """Run the public node (servers + tunnels) until interrupted."""
    try:
        asyncio.run(run_node())
    except KeyboardInterrupt:
        print("\nNode shut down; MCP servers and tunnels closed.")


if __name__ == "__main__":
    main()
