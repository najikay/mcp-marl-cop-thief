"""Control-panel backend: serves the panel, the live SSE TV, and status/challenge API.

Routes: ``/`` (control panel), ``/stream`` (broadcast-only Server-Sent-Events TV),
``/api/status`` (live node status JSON), ``/api/challenge`` (POST opponent details →
runs a cross-host challenge in a worker thread, streamed to the TV and emailed).
The UI can never mutate game state directly — it only posts a challenge request.
"""

from __future__ import annotations

import threading
from pathlib import Path

from starlette.applications import Starlette
from starlette.responses import FileResponse, JSONResponse, StreamingResponse
from starlette.routing import Route

_PANEL = Path(__file__).parent / "static" / "panel.html"


async def homepage(_request) -> FileResponse:
    """Serve the single-file control panel."""
    return FileResponse(_PANEL)


async def stream(_request) -> StreamingResponse:
    """Stream live turn snapshots from the broadcast bus as Server-Sent Events."""
    from cop_thief.ui import broadcast

    async def event_source():
        async for sse_chunk in broadcast.subscribe():
            yield sse_chunk

    return StreamingResponse(event_source(), media_type="text/event-stream")


async def status(_request) -> JSONResponse:
    """Return the live node status (servers, tunnels, URLs, tokens, game phase, email)."""
    from cop_thief.config import get_config_manager
    from cop_thief.ui.node_state import STATE

    snap = STATE.snapshot()
    snap["report_email"] = get_config_manager().setup.reporting.burner_email
    return JSONResponse(snap)


def _run_challenge(params: dict) -> None:
    """Worker thread: play one cross-host challenge, stream it, then email the report."""
    from cop_thief.infra.network.move_client import RemoteMoveClient
    from cop_thief.orchestrator.challenge_runner import ChallengeRunner
    from cop_thief.ui import broadcast
    from cop_thief.ui.node_state import STATE

    STATE.set_game("playing")
    try:
        runner = ChallengeRunner(
            params.get("our_group", "NajAmjad"), params.get("opp_group", "Opponent"),
            RemoteMoveClient(params["cop_url"], params.get("cop_token", "")),
            RemoteMoveClient(params["thief_url"], params.get("thief_token", "")),
            observer=broadcast.observe, announce=broadcast.banner, turn_delay=0.3)
        report = runner.run()
    except Exception as exc:  # thread boundary: surface any failure to the panel
        STATE.set_game("error", {"error": str(exc)})
        broadcast.banner(f"CHALLENGE FAILED: {exc}")
        return
    _email(report, params.get("email", ""))
    STATE.set_game("done", report)
    broadcast.banner(f"GAME DONE — {report['final_result']} — hash {report['agreement_sha256'][:12]}")


def _email(report: dict, recipient: str) -> None:
    """Email the report; a mail failure must not fail the (already played) game."""
    from google.auth.exceptions import GoogleAuthError

    from cop_thief.reporting import GmailApiReporter
    from cop_thief.ui import broadcast

    if not recipient:
        return
    try:
        reporter = GmailApiReporter()
        reporter.bootstrap_oauth()
        reporter.dispatch_payload(report, recipient)
    except (OSError, RuntimeError, ValueError, GoogleAuthError) as exc:
        broadcast.banner(f"Email skipped ({type(exc).__name__}).")


async def challenge(request) -> JSONResponse:
    """Start a cross-host challenge in a worker thread from posted opponent details."""
    params = await request.json()
    threading.Thread(target=_run_challenge, args=(params,), daemon=True).start()
    return JSONResponse({"status": "started"})


app = Starlette(routes=[
    Route("/", homepage),
    Route("/stream", stream),
    Route("/api/status", status),
    Route("/api/challenge", challenge, methods=["POST"]),
])


def main() -> None:
    """Run the control panel server on localhost:8800."""
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8800)


if __name__ == "__main__":
    main()
