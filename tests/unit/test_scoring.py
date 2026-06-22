"""Unit tests for the immutable scoring matrix."""

from __future__ import annotations

from cop_thief.config.models import ScoringConfig
from cop_thief.constants import SubGameOutcome
from cop_thief.domain.scoring import ScoringEngine


def _engine() -> ScoringEngine:
    return ScoringEngine(ScoringConfig(cop_win=20, thief_win=10, cop_loss=5, thief_loss=5))


def test_cop_win_scores():
    assert _engine().score(SubGameOutcome.COP_WINS) == (20, 5)


def test_thief_win_scores():
    assert _engine().score(SubGameOutcome.THIEF_WINS) == (5, 10)


def test_void_scores_nothing():
    assert _engine().score(SubGameOutcome.VOID_TECHNICAL) == (0, 0)
