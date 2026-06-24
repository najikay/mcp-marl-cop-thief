"""Single-process app: Cop+Thief MCP servers + live UI + the series pipeline.

One asyncio loop hosts the two MCP servers (:8001/:8002, tunneled) and the UI SSE
server (:8800, localhost). A background thread runs ONE full series (2 games × 3
matches, thief-first) whose turns flow — in-process — onto the shared broadcast
bus (live UI) and the audit log, emailing a report after each game.
Run: ``uv run python -m cop_thief.app``
"""

from __future__ import annotations

import asyncio
import threading

import uvicorn

from cop_thief.infra.network.dual_mcp_host import build_servers as build_mcp_servers
from cop_thief.orchestrator.series import SeriesRunner
from cop_thief.reporting import GameTelemetryLogger, GmailApiReporter
from cop_thief.servers.tools.move_tool import resolve_move
from cop_thief.ui import broadcast
from cop_thief.ui.server import app as ui_app

_UI_HOST = "127.0.0.1"
_UI_PORT = 8800
_TURN_DELAY = 0.35


def _build_reporter():
    """Build a Gmail reporter (vaulted token); disable email on any failure."""
    try:
        reporter = GmailApiReporter()
        reporter.bootstrap_oauth()
        return reporter
    except (OSError, RuntimeError, ValueError) as exc:
        print(f"Email disabled ({type(exc).__name__}): {exc}")
        return None


def _run_series_once() -> None:
    """Run one full series through the servers' move resolver, live to the UI."""
    runner = SeriesRunner(
        cop_provider=resolve_move, thief_provider=resolve_move,
        observer=broadcast.observe, logger=GameTelemetryLogger(),
        reporter=_build_reporter(), announce=broadcast.banner, turn_delay=_TURN_DELAY,
    )
    print(f"Series complete: {runner.run_series()}")


def _banner() -> None:
    rows = [
        "MARL COP & THIEF — series pipeline LIVE",
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
