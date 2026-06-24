"""TDD unit tests for the Homestretch subsystems (guard, reporter, GUI).

Scenarios:
1. SafetyGuard raises SubmissionSafetyException on a locked production address.
2. SafetyGuard permits the burner sandbox address unconditionally.
3. GmailApiReporter builds the canonical JSON handshake (facts + K3 hash + telemetry).
4. Headless tkinter: dispatch_update + root.update() render the canvas (no mainloop).
"""

from __future__ import annotations

from unittest import mock

import pytest

from cop_thief.domain.constants import AgentRole
from cop_thief.domain.grid import Grid
from cop_thief.domain.state import DecPomdpGameState
from cop_thief.reporting import (
    GmailApiReporter,
    SubmissionSafetyException,
    SubmissionSafetyGuard,
)


def test_guard_blocks_locked_production_address() -> None:
    """A 'haifa.ac.il'/'segal' address is rejected while locked."""
    guard = SubmissionSafetyGuard(locked=True)
    with pytest.raises(SubmissionSafetyException):
        guard.verify_safe_recipient("rmisegal@haifa.ac.il")


def test_guard_allows_burner_sandbox() -> None:
    """The burner sandbox address always passes, even when locked."""
    guard = SubmissionSafetyGuard(locked=True)
    assert guard.verify_safe_recipient("mcp.marl.telemetry@gmail.com") is None


def test_guard_config_default_and_passthrough() -> None:
    """Config-sourced lock, neutral passthrough, and unlocked production."""
    guard = SubmissionSafetyGuard()  # reads config -> locked True
    assert guard.locked is True
    assert guard.verify_safe_recipient("teammate@gmail.com") is None  # no blocked token
    unlocked = SubmissionSafetyGuard(locked=False)
    assert unlocked.verify_safe_recipient("rmisegal@haifa.ac.il") is None  # lock disengaged


def test_dispatch_payload_carries_group_name_in_subject_and_body() -> None:
    """The acting group name reaches the email subject line and the JSON body."""
    import base64

    captured = {}
    gatekeeper = mock.Mock()
    gatekeeper.execute = mock.Mock(side_effect=lambda fn, msg, service: captured.update(msg) or {})
    reporter = GmailApiReporter(
        guard=SubmissionSafetyGuard(locked=False), gatekeeper=gatekeeper, service=None
    )
    report = {"report_type": "bonus_game", "groups": {"ours": "NajAmjad", "opponent": "Beta"}}
    reporter.dispatch_payload(report, "mcp.marl.telemetry@gmail.com")
    mime = base64.urlsafe_b64decode(captured["raw"]).decode("utf-8")
    assert "subject: marl-cop-thief game report: najamjad" in mime.lower()
    assert "NajAmjad" in mime  # also present in the JSON body


def test_reporter_builds_canonical_json() -> None:
    """dispatch_game_report yields a structured handshake via the gatekeeper."""
    gatekeeper = mock.Mock()
    gatekeeper.execute = mock.Mock(return_value={"id": "msg-1", "status": "SENT"})
    reporter = GmailApiReporter(
        guard=SubmissionSafetyGuard(locked=True), gatekeeper=gatekeeper, service=None
    )
    state = DecPomdpGameState(
        cop_pos=(0, 0), thief_pos=(4, 4), grid=Grid(shape=(5, 5), barriers=frozenset({(2, 2)}))
    )

    report = reporter.dispatch_game_report(state, "mcp.marl.telemetry@gmail.com")
    assert report["report_type"] == "internal_game"
    assert report["facts"]["cop_pos"] == [0, 0]
    assert report["facts"]["thief_pos"] == [4, 4]
    assert report["facts"]["barriers"] == [[2, 2]]
    assert len(report["agreement_sha256"]) == 64
    assert set(report["telemetry"]) == {
        "input_accumulated", "output_accumulated", "estimated_cost_usd", "status"
    }
    assert report["_delivery"] == {"id": "msg-1", "status": "SENT"}
    gatekeeper.execute.assert_called_once()


def test_observer_gui_headless_update() -> None:
    """Instantiate the GUI, dispatch one update, and render via root.update()."""
    tk = pytest.importorskip("tkinter")
    from cop_thief.gui import ObserverGUI

    try:
        gui = ObserverGUI(grid_size=5)
    except tk.TclError:
        pytest.skip("no display available for tkinter")
    try:
        state = DecPomdpGameState(cop_pos=(1, 1), thief_pos=(3, 3))
        gui.dispatch_update(state, "advancing north", AgentRole.COP)
        gui._poll_queue()        # deterministic drain + render
        gui.root.update()        # process events; NEVER mainloop()
        assert len(gui.canvas.find_withtag("agents")) >= 2
        assert "advancing north" in gui.feed.get("1.0", "end")
    finally:
        gui.root.destroy()
