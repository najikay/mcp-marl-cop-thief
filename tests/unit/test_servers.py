"""In-process tests for the FastMCP Cop & Thief server tool handlers."""

from __future__ import annotations

from cop_thief.constants import Direction
from cop_thief.servers import CopServer, ThiefServer


def test_cop_server_role_and_tools_registered():
    server = CopServer()
    assert server.role == "cop"
    assert server.app.name == "cop-server"


def test_thief_server_role():
    assert ThiefServer().role == "thief"


def test_start_then_propose_returns_legal_turn():
    server = CopServer()
    server.start_sub_game("g1", [0, 0])
    out = server.propose_action("g1")
    assert out["action"] == "move"
    assert out["direction"] in {d.name for d in Direction}
    assert out["message"].startswith("Cop:")
    assert "next_cell" not in out  # internal field stripped before returning


def test_receive_message_updates_belief_and_biases_move():
    server = CopServer()
    server.start_sub_game("g1", [0, 0])
    server.receive_message("g1", "I'm slipping through the south-east area")
    out = server.propose_action("g1")
    assert out["direction"] in {"SE", "S", "E"}  # heads toward believed corner


def test_agree_on_report_handshake():
    server = ThiefServer()
    assert server.agree_on_report({"mutual_agreement": True}) == {"agree": True}
    assert server.agree_on_report({"mutual_agreement": False}) == {"agree": False}


def test_token_authorization():
    open_server = CopServer()
    assert open_server.authorized(None)  # no token configured -> open
    secured = CopServer(token="s3cret")
    assert secured.authorized("s3cret")
    assert not secured.authorized("wrong")
