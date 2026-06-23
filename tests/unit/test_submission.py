"""Unit tests for submission metadata loading and report wiring."""

from __future__ import annotations

import json

from cop_thief.config.submission import SubmissionConfig, load_submission
from cop_thief.sdk import CopThiefSDK


def test_loads_real_submission_file():
    sub = load_submission()
    assert sub.group_name  # non-empty
    assert isinstance(sub.students, list)


def test_missing_file_returns_defaults(tmp_path):
    sub = load_submission(tmp_path / "nope.json")
    assert isinstance(sub, SubmissionConfig)
    assert sub.students == []


def test_partial_file_fills_defaults(tmp_path):
    path = tmp_path / "submission.json"
    path.write_text(json.dumps({"group_name": "Team-X"}), encoding="utf-8")
    sub = load_submission(path)
    assert sub.group_name == "Team-X"
    assert sub.cop_mcp_url.startswith("http")  # default filled in


def test_report_includes_students(small_config):
    sdk = CopThiefSDK(config=small_config)
    report = sdk.build_internal_report(
        sdk.play_game(),
        group_name="Team-X",
        github_repo="https://github.com/x/y",
        cop_mcp_url="http://a",
        thief_mcp_url="http://b",
        students=["Amjad", "Naji"],
    )
    assert json.loads(report.to_json())["students"] == ["Amjad", "Naji"]
