"""InternalReport — the per-group game JSON schema (lecture §9.1).

Shape::

    {"group_name", "students", "github_repo", "cop_mcp_url", "thief_mcp_url",
     "timezone", "sub_games": [...], "totals": {"cop", "thief"}}
"""

from __future__ import annotations

from dataclasses import dataclass, field

from ...orchestrator.game_loop import GameResult
from .base_report import BaseReport


@dataclass
class InternalReport(BaseReport):
    """Assemble the internal game report from a :class:`GameResult`."""

    group_name: str
    github_repo: str
    cop_mcp_url: str
    thief_mcp_url: str
    result: GameResult
    students: list[str] = field(default_factory=list)
    timezone: str = "Asia/Jerusalem"

    @classmethod
    def from_result(
        cls,
        result: GameResult,
        group_name: str,
        github_repo: str,
        cop_mcp_url: str,
        thief_mcp_url: str,
        students: list[str] | None = None,
    ) -> InternalReport:
        """Build the report from a played game and submission metadata."""
        return cls(
            group_name=group_name,
            github_repo=github_repo,
            cop_mcp_url=cop_mcp_url,
            thief_mcp_url=thief_mcp_url,
            result=result,
            students=students or [],
        )

    def to_dict(self) -> dict:
        """Serialise to the internal JSON schema with per-sub-game detail."""
        return {
            "version": self.version,
            "group_name": self.group_name,
            "students": list(self.students),
            "github_repo": self.github_repo,
            "cop_mcp_url": self.cop_mcp_url,
            "thief_mcp_url": self.thief_mcp_url,
            "timezone": self.timezone,
            "sub_games": [self._sub_game_dict(r) for r in self.result.sub_games],
            "totals": {"cop": self.result.cop_total, "thief": self.result.thief_total},
        }

    @staticmethod
    def _sub_game_dict(record) -> dict:
        return {
            "index": record.index,
            "outcome": record.outcome.value,
            "cop_score": record.cop_score,
            "thief_score": record.thief_score,
            "moves": record.moves,
        }
