"""SubmissionConfig — one place for the team's report metadata.

Group name, students, GitHub repo and the two MCP URLs live in
``config/submission.json`` so the final report isn't assembled from scattered CLI
flags. The file is optional: if absent, sensible defaults are returned and the
CLIs still work.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from .. import __version__

_DEFAULT_PATH = Path(__file__).resolve().parents[3] / "config" / "submission.json"


@dataclass(frozen=True)
class SubmissionConfig:
    """Team metadata that decorates the JSON report."""

    group_name: str = "Team-Alpha"
    github_repo: str = "https://github.com/example/marl-cop-thief"
    students: list[str] = field(default_factory=list)
    cop_mcp_url: str = "http://localhost:8001"
    thief_mcp_url: str = "http://localhost:8002"
    version: str = __version__

    @classmethod
    def from_dict(cls, data: dict) -> SubmissionConfig:
        """Build from raw JSON, tolerating missing keys (defaults fill in)."""
        defaults = cls()
        return cls(
            group_name=str(data.get("group_name", defaults.group_name)),
            github_repo=str(data.get("github_repo", defaults.github_repo)),
            students=list(data.get("students", [])),
            cop_mcp_url=str(data.get("cop_mcp_url", defaults.cop_mcp_url)),
            thief_mcp_url=str(data.get("thief_mcp_url", defaults.thief_mcp_url)),
            version=str(data.get("version", __version__)),
        )


def load_submission(path: str | Path | None = None) -> SubmissionConfig:
    """Load submission metadata, or return defaults if the file is absent."""
    target = Path(path) if path is not None else _DEFAULT_PATH
    if not target.exists():
        return SubmissionConfig()
    return SubmissionConfig.from_dict(json.loads(target.read_text(encoding="utf-8")))
