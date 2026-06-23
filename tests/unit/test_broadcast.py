"""TDD unit test for the SSE broadcast packet schema (barriers + status)."""

from __future__ import annotations

from cop_thief.domain.grid import Grid
from cop_thief.domain.state import DecPomdpGameState
from cop_thief.ui.broadcast import make_packet


def test_make_packet_includes_barriers_and_status() -> None:
    """A live snapshot carries barrier cells, status, epistemic and prose split."""
    state = DecPomdpGameState(
        cop_pos=(1, 1), thief_pos=(3, 3), grid=Grid(shape=(5, 5), barriers=frozenset({(2, 2)}))
    )
    packet = make_packet(state, "I edge west", informed=True)
    assert packet["barriers"] == [[2, 2]]
    assert packet["status"] == "live"
    assert packet["epistemic"] == "Q-Policy"
    assert packet["cop"] == [1, 1] and packet["thief"] == [3, 3]


def test_make_packet_capture_status() -> None:
    """Co-located agents report a 'capture' status."""
    state = DecPomdpGameState(cop_pos=(2, 2), thief_pos=(2, 2))
    assert make_packet(state, "got you", informed=False)["status"] == "capture"
