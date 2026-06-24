"""TDD unit tests for the AgentRoster and the real MatchOrchestrator."""

from __future__ import annotations

from cop_thief.domain.constants import AgentRole, SubGameOutcome
from cop_thief.domain.strategy.roster import AgentRoster
from cop_thief.orchestrator.match import MatchOrchestrator


def test_roster_three_variants() -> None:
    """A roster fields 3 distinct strategy variants, indexable per match."""
    roster = AgentRoster(AgentRole.COP)
    assert len(roster) == 3
    assert roster.labels == ["aggressive", "balanced", "defensive"]
    assert roster.agent(0) is not roster.agent(1)
    assert roster.agent(3) is roster.agent(0)  # wraps around


def test_match_is_thief_first() -> None:
    """The very first move of a match is the Thief's (turn then flips to Cop)."""
    recorded: list = []
    orch = MatchOrchestrator(observer=lambda s, p, i: recorded.append(s), turn_delay=0.0)
    cop, thief = AgentRoster(AgentRole.COP), AgentRoster(AgentRole.THIEF)
    orch.play_match(cop.agent(0), thief.agent(0))
    assert recorded, "expected at least one broadcast turn"
    assert recorded[0].turn_role is AgentRole.COP  # thief already moved -> role flipped to cop
    assert recorded[0].turn_counter == 1


def test_play_game_three_matches() -> None:
    """A game is exactly 3 matches, each ending in a valid terminal outcome."""
    orch = MatchOrchestrator(turn_delay=0.0)
    cop, thief = AgentRoster(AgentRole.COP), AgentRoster(AgentRole.THIEF)
    outcomes = orch.play_game(cop, thief)
    assert len(outcomes) == 3
    assert all(isinstance(o, SubGameOutcome) for o in outcomes)
    valid = {SubGameOutcome.COP_WINS, SubGameOutcome.THIEF_WINS, SubGameOutcome.THIEF_TRAPPED}
    assert all(o in valid for o in outcomes)
