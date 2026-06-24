"""TDD: NodeState live status holder for the control panel."""

from __future__ import annotations

from cop_thief.ui.node_state import NodeState


def test_initial_state_is_down_and_idle() -> None:
    """A fresh node reports servers/tunnels down and the game idle."""
    snap = NodeState().snapshot()
    assert snap["servers_up"] is False
    assert snap["tunnels_up"] is False
    assert snap["game_status"] == "idle"
    assert snap["cop_url"] == ""


def test_boot_sequence_updates_snapshot() -> None:
    """Marking servers/tunnels up surfaces the public URLs in the snapshot."""
    state = NodeState()
    state.set_servers_up()
    state.set_tunnels("https://c.example/mcp/", "https://t.example/mcp/")
    snap = state.snapshot()
    assert snap["servers_up"] is True and snap["tunnels_up"] is True
    assert snap["cop_url"] == "https://c.example/mcp/"
    assert snap["thief_url"] == "https://t.example/mcp/"


def test_game_status_and_result_tracked() -> None:
    """Game phase transitions and the last result are retained."""
    state = NodeState()
    state.set_game("playing")
    assert state.snapshot()["game_status"] == "playing"
    state.set_game("done", {"final_result": "ours"})
    snap = state.snapshot()
    assert snap["game_status"] == "done"
    assert snap["last_result"] == {"final_result": "ours"}


def test_tokens_read_from_environment(monkeypatch) -> None:
    """Snapshot exposes the current bearer tokens so they can be shared."""
    monkeypatch.setenv("COP_MCP_TOKEN", "abc123")
    monkeypatch.setenv("THIEF_MCP_TOKEN", "def456")
    snap = NodeState().snapshot()
    assert snap["cop_token"] == "abc123"
    assert snap["thief_token"] == "def456"
