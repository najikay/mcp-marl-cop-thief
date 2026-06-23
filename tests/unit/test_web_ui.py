"""Smoke test for the web UI Starlette app builder."""

from __future__ import annotations

from cop_thief.ui import build_app


def test_app_exposes_page_and_event_routes():
    app = build_app()
    paths = {route.path for route in app.routes}
    assert "/" in paths  # the page
    assert "/events" in paths  # the SSE stream
