"""BonusReport — the inter-group bonus JSON schema (lecture §9.2).

Pure data in, JSON out: the caller (SDK) flattens a series result into the
``sub_games`` list and supplies both groups' metadata, so this layer stays
independent of the orchestrator. The bonus claim is derived from the totals.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .agreement import compute_bonus_claim
from .base_report import BaseReport


@dataclass
class BonusReport(BaseReport):
    """Assemble the bonus-game report shared (identically) by both groups."""

    group_1: str
    group_2: str
    github_repo_group_1: str
    github_repo_group_2: str
    mcp_url_group_1_cop: str
    mcp_url_group_1_thief: str
    mcp_url_group_2_cop: str
    mcp_url_group_2_thief: str
    sub_games: list[dict]
    totals_by_group: dict[str, int]
    mutual_agreement: bool = True
    students_group_1: list[str] = field(default_factory=list)
    students_group_2: list[str] = field(default_factory=list)
    timezone: str = "Asia/Jerusalem"

    def to_dict(self) -> dict:
        """Serialise to the inter-group bonus schema."""
        return {
            "report_type": "bonus_game",
            "version": self.version,
            "groups": {"group_1": self.group_1, "group_2": self.group_2},
            "github_repo_group_1": self.github_repo_group_1,
            "github_repo_group_2": self.github_repo_group_2,
            "mcp_url_group_1_cop": self.mcp_url_group_1_cop,
            "mcp_url_group_1_thief": self.mcp_url_group_1_thief,
            "mcp_url_group_2_cop": self.mcp_url_group_2_cop,
            "mcp_url_group_2_thief": self.mcp_url_group_2_thief,
            "timezone": self.timezone,
            "students_group_1": list(self.students_group_1),
            "students_group_2": list(self.students_group_2),
            "sub_games": self.sub_games,
            "totals_by_group": self.totals_by_group,
            "bonus_claim": compute_bonus_claim(self.totals_by_group),
            "mutual_agreement": self.mutual_agreement,
        }
