"""Unit tests for the natural-language protocol (encoder, parser, belief)."""

from __future__ import annotations

from cop_thief.constants import AgentRole, Direction
from cop_thief.domain.grid import Cell, Grid
from cop_thief.domain.nl import BeliefUpdate, NLEncoder, NLParser


def test_encoder_emits_no_coordinates():
    msg = NLEncoder().describe(Cell(0, 0), 6, 6, AgentRole.COP, Direction.S)
    assert "north" in msg and "west" in msg
    assert not any(ch.isdigit() for ch in msg)  # never numeric coordinates


def test_encoder_centre_region():
    msg = NLEncoder().describe(Cell(2, 2), 5, 5, AgentRole.THIEF, Direction.E)
    assert "centre" in msg


def test_round_trip_recovers_region():
    msg = NLEncoder().describe(Cell(0, 0), 6, 6, AgentRole.COP, Direction.S)
    belief = NLParser().parse(msg)
    assert belief.region_row == "north"
    assert belief.region_col == "west"
    assert belief.confidence > 0


def test_parser_defensive_default_on_noise():
    belief = NLParser().parse("hello there, nice weather today")
    assert belief == BeliefUpdate.unknown()
    assert belief.confidence == 0.0


def test_parser_detects_barrier_mention():
    belief = NLParser().parse("I sealed the wall to my south")
    assert belief.barrier_mentioned
    assert belief.region_row == "south"


def test_belief_estimate_cell_projects_region():
    belief = BeliefUpdate("south", "east", None, False, 0.6)
    cell = belief.estimate_cell(Grid(6, 6))
    assert cell == Cell(5, 5)


def test_belief_unknown_has_no_cell():
    assert BeliefUpdate.unknown().estimate_cell(Grid(5, 5)) is None
