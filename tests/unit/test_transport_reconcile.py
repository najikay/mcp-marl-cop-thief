"""TDD: real MCP-SSE move transport (in-memory) + mutual-agreement reconcile."""

from __future__ import annotations

import asyncio

from cop_thief.infra.network.move_client import RemoteMoveClient, fetch_remote_move
from cop_thief.orchestrator.reconcile import canonical_hash, reconcile_agreement
from cop_thief.servers import create_cop_server, create_thief_server
from cop_thief.servers.auth import SecurityMiddleware

_OBS = {"role": "cop", "grid": [5, 5], "cop": [0, 0], "thief": [4, 4], "barriers": []}


def _server(factory):
    """Build a server whose middleware accepts the fixed test token 'secret'."""
    return factory(security=SecurityMiddleware(get_env=lambda key, default="": "secret"))


def test_remote_move_client_calls_request_move_over_client() -> None:
    """The challenger adapter returns treaty prose from the Cop's request_move tool."""
    client = RemoteMoveClient(_server(create_cop_server), "secret")
    assert client(_OBS).startswith("[INTENT:")


def test_fetch_remote_move_thief_server() -> None:
    """fetch_remote_move drives the Thief server's request_move tool directly."""
    obs = {**_OBS, "role": "thief"}
    prose = asyncio.run(fetch_remote_move(_server(create_thief_server), obs, "secret"))
    assert "[INTENT:" in prose


def test_reconcile_match_keeps_totals_and_result() -> None:
    """Identical agreement hashes keep totals and mark mutual_agreement true."""
    report = {"sub_games": [{"sub_game": 1, "outcome": "cop_wins"}],
              "totals": {"ours": 20, "opponent": 5}, "final_result": "ours"}
    report["agreement_sha256"] = canonical_hash(report["sub_games"])
    out = reconcile_agreement(report, dict(report))
    assert out["mutual_agreement"] is True
    assert out["totals"] == {"ours": 20, "opponent": 5}
    assert out["final_result"] == "ours"


def test_reconcile_mismatch_is_both_lose() -> None:
    """Divergent reports force mutual_agreement false and a 0/0 'both_lose' line."""
    ours = {"sub_games": [{"sub_game": 1, "outcome": "cop_wins"}],
            "totals": {"ours": 20, "opponent": 5}, "final_result": "ours"}
    ours["agreement_sha256"] = canonical_hash(ours["sub_games"])
    theirs = {"sub_games": [{"sub_game": 1, "outcome": "thief_wins"}]}
    theirs["agreement_sha256"] = canonical_hash(theirs["sub_games"])
    out = reconcile_agreement(ours, theirs)
    assert out["mutual_agreement"] is False
    assert out["final_result"] == "both_lose"
    assert out["totals"] == {"ours": 0, "opponent": 0}
    assert out["partner_agreement_sha256"] == theirs["agreement_sha256"]
