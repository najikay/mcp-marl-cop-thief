"""Tests for the per-move frame API that feeds the GUI."""

from __future__ import annotations

from cop_thief.sdk import CopThiefSDK


def test_record_sub_game_returns_frames(small_config):
    frames = CopThiefSDK(config=small_config).record_sub_game()
    assert len(frames) >= 2  # at least a start frame and one move
    assert frames[0]["message"] is None  # initial frame has no message
    assert all(m["message"] for m in frames[1:])  # every move carries NL text


def test_frame_structure_is_within_bounds(small_config):
    rows, cols = small_config.grid_size
    frames = CopThiefSDK(config=small_config).record_sub_game()
    for frame in frames:
        for key in ("cop", "thief", "barriers"):
            assert key in frame
        r, c = frame["cop"]
        assert 0 <= r < rows and 0 <= c < cols
