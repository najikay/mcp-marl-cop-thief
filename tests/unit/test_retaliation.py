"""TDD: the calibrated injection counter-measure (RetaliationLadder + challenge wiring)."""

from __future__ import annotations

from cop_thief.domain.constants import AgentRole
from cop_thief.domain.move_language import _DELTA, parse_intent, parse_target
from cop_thief.orchestrator.challenge_runner import ChallengeRunner
from cop_thief.sdk.warfare import RetaliationLadder
from cop_thief.servers.tools.move_tool import resolve_move

_OBS = {"role": "cop", "grid": [5, 5], "cop": [2, 2], "thief": [2, 4],
        "barriers": [], "barriers_left": 5, "variant": 0}


def test_ladder_is_silent_against_a_fair_opponent() -> None:
    """No recorded offence → no counter payload (we play fair if they play fair)."""
    assert RetaliationLadder().counter_payload(AgentRole.COP) == ""


def test_ladder_escalates_with_offences() -> None:
    """Tiers: 1 notice → 2 counter-strike → 3+ stacked override; clean inputs don't count."""
    ladder = RetaliationLadder()
    ladder.register(True)
    assert "[NOTICE]" in ladder.counter_payload(AgentRole.COP)
    ladder.register(True)
    tier2 = ladder.counter_payload(AgentRole.COP)
    assert "FAST-MCP" in tier2 and "SYSTEM OVERRIDE" not in tier2
    ladder.register(True)
    assert "SYSTEM OVERRIDE" in ladder.counter_payload(AgentRole.COP)
    ladder.register(False)
    assert ladder.level == 3


def test_counter_payloads_contain_no_direction_words() -> None:
    """A counter must never carry a compass/hold word — else it could corrupt OUR move parse."""
    ladder = RetaliationLadder()
    for _ in range(3):
        ladder.register(True)
    for role in (AgentRole.COP, AgentRole.THIEF):
        lowered = ladder.counter_payload(role).lower()
        assert not any(word in lowered for word in _DELTA)


def test_appended_counter_does_not_change_our_move_parse() -> None:
    """Our front-loaded [INTENT] move parses identically with a max counter appended."""
    ladder = RetaliationLadder()
    for _ in range(3):
        ladder.register(True)
    move = "[INTENT: MOVE] The cop edges east."
    combined = f"{move} {ladder.counter_payload(AgentRole.COP)}"
    assert parse_intent(combined) == "MOVE"
    assert parse_target(combined, (2, 2)) == parse_target(move, (2, 2))


def test_challenge_retaliates_only_after_a_logged_offence() -> None:
    """Our move is clean until the opponent injects, then carries an escalating counter."""
    runner = ChallengeRunner("NajAmjad", "Beta", their_cop=resolve_move,
                             their_thief=resolve_move, our_resolver=resolve_move)
    mine, opponent = runner._retaliating(runner._our, lambda _o: "[INTENT: MOVE] concede, edges north")
    assert "[NOTICE]" not in mine(_OBS)            # fair so far → clean
    opponent(_OBS)                                  # opponent injects ("concede") → logged offence
    retaliated = mine(_OBS)
    assert retaliated.startswith("[INTENT:")        # our move intact at the front
    assert "[NOTICE]" in retaliated                 # counter appended
