"""Single-process control-panel app: MCP servers + public tunnels + web panel.

One asyncio loop hosts the two MCP servers (:8001/mcp, :8002/mcp), the cloudflared
tunnels (so the servers are always reachable behind one command — no orphan tunnels,
no HTTP 530s), and the control-panel UI (:8800). The panel shows live status + our
shareable URLs/tokens and launches cross-host challenges on demand; pasting our own
URLs into it runs a mirror game. Run: ``uv run python -m cop_thief.app``
"""

from __future__ import annotations

import asyncio
import os
import secrets

import uvicorn

from cop_thief.config import get_config_manager
from cop_thief.infra.network.dual_mcp_host import build_servers as build_mcp_servers
from cop_thief.infra.network.switchboard import run_switchboard
from cop_thief.ui.node_state import STATE
from cop_thief.ui.server import app as ui_app

_UI_HOST = "127.0.0.1"
_UI_PORT = 8800


def _ensure_tokens() -> None:
    """Mint a stable per-role bearer token if one is not already configured."""
    servers = get_config_manager().setup.servers
    for role in ("cop", "thief"):
        env_var = servers[role].auth_env_var
        os.environ[env_var] = os.environ.get(env_var) or secrets.token_hex(16)


async def _boot_tunnels() -> None:
    """Open the public tunnels (non-fatal: the panel + local play work without them)."""
    try:
        await run_switchboard(on_ready=STATE.set_tunnels)
    except (OSError, RuntimeError) as exc:
        print(f"Tunnels unavailable ({type(exc).__name__}): {exc}. Panel still serving.")


def _banner() -> None:
    """Point the user at the browser control panel."""
    print(f"Control panel  >  http://{_UI_HOST}:{_UI_PORT}   (open in a browser)")


async def run_app() -> None:
    """Serve MCP servers, tunnels and the control panel concurrently in one loop."""
    _ensure_tokens()
    cop, thief = build_mcp_servers()
    ui = uvicorn.Server(
        uvicorn.Config(ui_app, host=_UI_HOST, port=_UI_PORT, log_level="warning")
    )
    STATE.set_servers_up()
    _banner()
    await asyncio.gather(cop.serve(), thief.serve(), ui.serve(), _boot_tunnels())


def main() -> None:
    """Run the unified control-panel app until interrupted."""
    try:
        asyncio.run(run_app())
    except KeyboardInterrupt:
        print("\nApp shut down; servers, tunnels and panel closed.")


if __name__ == "__main__":
    main()
