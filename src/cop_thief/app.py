"""Single-process app: Cop+Thief MCP servers + live UI + the series pipeline.

One asyncio loop hosts the two MCP servers (:8001/:8002, tunneled) and the UI SSE
server (:8800, localhost). A background thread runs ONE full game (6 sub-games:
3 as Cop on the HOME leg + 3 as Thief on the AWAY leg, thief-first) whose turns
flow — in-process — onto the shared broadcast bus (live UI) and the audit log,
emailing one merged report at the end.
Run: ``uv run python -m cop_thief.app``
"""

from __future__ import annotations

import asyncio
import os
import secrets
import threading
import time

import uvicorn

from cop_thief.config import get_config_manager
from cop_thief.infra.network.dual_mcp_host import build_servers as build_mcp_servers
from cop_thief.infra.network.move_client import RemoteMoveClient
from cop_thief.orchestrator.reconcile import reconcile_agreement
from cop_thief.orchestrator.series import SeriesRunner
from cop_thief.reporting import GameTelemetryLogger, GmailApiReporter
from cop_thief.ui import broadcast
from cop_thief.ui.server import app as ui_app

_UI_HOST = "127.0.0.1"
_UI_PORT = 8800
_TURN_DELAY = 0.35
_COP_SSE = "http://127.0.0.1:8001/sse"
_THIEF_SSE = "http://127.0.0.1:8002/sse"
_STARTUP_GRACE = 3.0


def _ensure_token(env_var: str) -> str:
    """Return the role's bearer token, minting a process-local one if unset."""
    value = os.environ.get(env_var) or secrets.token_hex(16)
    os.environ[env_var] = value
    return value


def _build_reporter():
    """Build a Gmail reporter (vaulted token); disable email on any auth failure.

    A disabled/expired OAuth client must NOT crash the game thread — we degrade to
    'email off' and let the series run and render on the UI regardless.
    """
    from google.auth.exceptions import GoogleAuthError

    try:
        reporter = GmailApiReporter()
        reporter.bootstrap_oauth()
        return reporter
    except (OSError, RuntimeError, ValueError, GoogleAuthError) as exc:
        print(f"Email disabled ({type(exc).__name__}): {exc} — game continues without email.")
        return None


def _run_series_once() -> None:
    """Run one full game over REAL MCP-over-SSE transport, then reconcile (live UI).

    Each move is fetched by challenging our Cop/Thief ``/sse`` endpoints with the
    ``request_move`` tool (identical to challenging a partner's tunnel URL); the
    merged report is then reconciled (mirror mode: we are our own partner).
    """
    servers = get_config_manager().setup.servers
    cop = RemoteMoveClient(_COP_SSE, _ensure_token(servers["cop"].auth_env_var))
    thief = RemoteMoveClient(_THIEF_SSE, _ensure_token(servers["thief"].auth_env_var))
    time.sleep(_STARTUP_GRACE)  # let the SSE servers bind before we challenge them
    runner = SeriesRunner(
        cop_provider=cop, thief_provider=thief,
        observer=broadcast.observe, logger=GameTelemetryLogger(),
        reporter=_build_reporter(), announce=broadcast.banner, turn_delay=_TURN_DELAY,
    )
    verdict = reconcile_agreement(report := runner.run_series(), report)
    broadcast.banner(f"MUTUAL AGREEMENT: {verdict['mutual_agreement']} — {verdict['final_result']}")
    print(f"Game complete (agreed={verdict['mutual_agreement']}): {verdict['totals']}")


def _banner() -> None:
    rows = [
        "MARL COP & THIEF — game pipeline LIVE",
        "1 GAME = 6 sub-games  (3 as COP / home + 3 as THIEF / away)",
        f"UI    >  http://{_UI_HOST}:{_UI_PORT}",
        "Cop   MCP >  http://127.0.0.1:8001   (tunneled)",
        "Thief MCP >  http://127.0.0.1:8002   (tunneled)",
    ]
    width = max(len(r) for r in rows) + 2
    bar = "═" * width
    print(f"╔{bar}╗")
    for row in rows:
        print(f"║ {row.ljust(width - 1)}║")
    print(f"╚{bar}╝")


async def run_app() -> None:
    """Serve both MCP servers and the UI concurrently; run one series in the background."""
    cop, thief = build_mcp_servers()
    ui = uvicorn.Server(
        uvicorn.Config(ui_app, host=_UI_HOST, port=_UI_PORT, log_level="warning")
    )
    threading.Thread(target=_run_series_once, daemon=True).start()
    _banner()
    await asyncio.gather(cop.serve(), thief.serve(), ui.serve())


def main() -> None:
    """Run the unified app until interrupted."""
    try:
        asyncio.run(run_app())
    except KeyboardInterrupt:
        print("\nApp shut down; MCP servers and UI closed.")


if __name__ == "__main__":
    main()
