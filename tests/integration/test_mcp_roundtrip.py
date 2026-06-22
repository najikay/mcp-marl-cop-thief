"""Integration: an orchestrator routing free-NL between two MCP servers.

This mirrors the bonus setup — Group A's Cop server vs Group B's Thief server —
exchanging only natural-language messages through the contract tools.
"""

from __future__ import annotations

from cop_thief.constants import Direction
from cop_thief.servers import CopServer, ThiefServer

_VALID_DIRS = {d.name for d in Direction}


def test_cross_server_nl_exchange_runs():
    cop = CopServer()
    thief = ThiefServer()
    cop.start_sub_game("g1", [0, 0])
    thief.start_sub_game("g1", [4, 4])

    cop_msg = "Cop: starting in the north-west area."
    for _ in range(5):
        thief.receive_message("g1", cop_msg)
        thief_turn = thief.propose_action("g1")
        assert thief_turn["direction"] in _VALID_DIRS
        assert thief_turn["action"] == "move"  # the thief never places barriers

        cop.receive_message("g1", thief_turn["message"])
        cop_turn = cop.propose_action("g1")
        assert cop_turn["direction"] in _VALID_DIRS
        assert cop_turn["message"].startswith("Cop:")
        cop_msg = cop_turn["message"]


def test_messages_carry_no_coordinates():
    thief = ThiefServer()
    thief.start_sub_game("g1", [2, 2])
    msg = thief.propose_action("g1")["message"]
    assert not any(ch.isdigit() for ch in msg)  # natural language only (K1)
