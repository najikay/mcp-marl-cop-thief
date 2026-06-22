"""BonusSeriesController — the inter-group role-swap competition (lecture §12).

A bonus series is 6 sub-games between two groups: the first half with Group A's
Cop vs Group B's Thief, the second half with the roles swapped. Each group's
points are tallied across both halves. A :class:`GroupSide` supplies agent
factories (locally both are our SDK; in the real bonus one side is driven over a
remote MCP server).
"""

from __future__ import annotations

import random
from collections.abc import Callable
from dataclasses import dataclass, field

from ..config.models import GameConfig
from ..domain.agents import CopAgent, ThiefAgent
from .game_loop import GameLoopController, SubGameRecord


@dataclass
class GroupSide:
    """One competing group: its metadata plus how to build its agents."""

    name: str
    github_repo: str
    cop_mcp_url: str
    thief_mcp_url: str
    cop_factory: Callable[[], CopAgent]
    thief_factory: Callable[[], ThiefAgent]
    students: list[str] = field(default_factory=list)


@dataclass
class BonusSeriesResult:
    """Per-half records and the points tallied for each group."""

    group_a: str
    group_b: str
    first_half: list[SubGameRecord]
    second_half: list[SubGameRecord]
    totals_by_group: dict[str, int]

    def to_sub_game_dicts(self) -> list[dict]:
        """Flatten both halves into tagged, JSON-ready sub-game entries."""
        rows = [self._row(r, self.group_a, self.group_b) for r in self.first_half]
        rows += [self._row(r, self.group_b, self.group_a) for r in self.second_half]
        for index, row in enumerate(rows, start=1):
            row["index"] = index
        return rows

    @staticmethod
    def _row(record: SubGameRecord, cop_group: str, thief_group: str) -> dict:
        return {
            "cop_group": cop_group,
            "thief_group": thief_group,
            "outcome": record.outcome.value,
            "cop_score": record.cop_score,
            "thief_score": record.thief_score,
            "moves": record.moves,
        }


class BonusSeriesController:
    """Run a bilateral role-swap series and tally points per group."""

    def __init__(self, config: GameConfig, side_a: GroupSide, side_b: GroupSide) -> None:
        self._config = config
        self._a = side_a
        self._b = side_b

    def play_series(self, rng: random.Random | None = None) -> BonusSeriesResult:
        """Play 3 sub-games each way (config ``num_games`` split in half)."""
        rng = rng or random.Random(self._config.seed)
        half = self._config.num_games // 2
        first = self._play(self._a.cop_factory(), self._b.thief_factory(), half, rng)
        second = self._play(self._b.cop_factory(), self._a.thief_factory(), half, rng)
        a_points = self._sum(first, "cop") + self._sum(second, "thief")
        b_points = self._sum(first, "thief") + self._sum(second, "cop")
        totals = {self._a.name: a_points, self._b.name: b_points}
        return BonusSeriesResult(self._a.name, self._b.name, first, second, totals)

    def _play(self, cop, thief, count, rng) -> list[SubGameRecord]:
        return GameLoopController(self._config, cop, thief).play_sub_games(count, rng)

    @staticmethod
    def _sum(records: list[SubGameRecord], role: str) -> int:
        return sum(getattr(r, f"{role}_score") for r in records)
