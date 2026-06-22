"""Immutable belief model produced by the defensive NL parser."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict

from cop_thief.domain.constants import Direction


class BeliefUpdate(BaseModel):
    """A compact, immutable sufficient statistic of the opponent's position.

    Collapses the (intractable) full Bayesian posterior into four decision-ready
    fields, mirroring ``PRD_nl_protocol.md``.
    """

    model_config = ConfigDict(frozen=True)

    estimated_direction: Direction
    distance_band: str
    inferred_barriers: frozenset[tuple[int, int]]
    confidence_score: float
