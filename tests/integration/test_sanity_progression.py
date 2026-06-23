"""Phase-9 live integration: sanity ladder + burner loopback dry-run.

LLM transport is mocked (no network/keys); the FastMCP servers run as real
in-memory async clients, and the pursuit mechanics + Q-table run for real.
"""

from __future__ import annotations

import asyncio
from pathlib import Path
from unittest import mock

from fastmcp import Client

from cop_thief.domain.constants import Direction
from cop_thief.domain.grid import Grid
from cop_thief.domain.state import DecPomdpGameState
from cop_thief.domain.strategy import QTableStrategy
from cop_thief.orchestrator.controller import GameLoopController
from cop_thief.orchestrator.firewall import CognitiveFirewall
from cop_thief.orchestrator.models import BeliefUpdate
from cop_thief.reporting import GmailApiReporter, SubmissionSafetyGuard
from cop_thief.sdk import CopThiefSDK
from cop_thief.servers import SecurityMiddleware, create_cop_server, create_thief_server

_LADDER = [(2, 2), (3, 3), (4, 4), (5, 5)]


def _belief() -> BeliefUpdate:
    return BeliefUpdate(
        estimated_direction=Direction.STAY,
        distance_band="UNKNOWN",
        inferred_barriers=frozenset(),
        confidence_score=0.0,
    )


def _mock_controller(grid: tuple[int, int], tmp_path: Path) -> GameLoopController:
    encoder = mock.Mock()
    encoder.generate_prose_transmission = mock.Mock(return_value="qualitative prose")
    parser = mock.Mock()
    parser.parse_inbound_prose = mock.Mock(return_value=_belief())
    firewall = CognitiveFirewall(ledger_file=tmp_path / f"ledger_{grid[0]}.json")
    sdk = CopThiefSDK()
    sdk.initialize_match()
    strategy = QTableStrategy(grid_shape=grid)
    return GameLoopController(
        sdk=sdk, encoder=encoder, parser=parser, firewall=firewall, strategy=strategy
    )


async def _probe_servers() -> None:
    """Connect to both FastMCP servers via in-memory async clients."""
    security = SecurityMiddleware(get_env=lambda key, default="": "secret")
    sdk = CopThiefSDK()
    sdk.initialize_match()
    cop = create_cop_server(sdk=sdk, security=security)
    thief = create_thief_server(sdk=sdk, security=security)
    async with Client(cop) as client:
        res = await client.call_tool(
            "transmit_thief_prose", {"prose_payload": "near the west wall", "auth_token": "secret"}
        )
        assert "cop" in str(getattr(res, "data", res)).lower()
    async with Client(thief) as client:
        res = await client.call_tool(
            "transmit_cop_prose", {"prose_payload": "closing from north", "auth_token": "secret"}
        )
        assert "thief" in str(getattr(res, "data", res)).lower()


def test_sanity_ladder(tmp_path: Path) -> None:
    """Run full pursuits across the grid ladder; assert bounds + Q accumulation."""
    for grid in _LADDER:
        controller = _mock_controller(grid, tmp_path)
        sdk = controller._sdk
        state = DecPomdpGameState(
            cop_pos=(0, 0), thief_pos=(grid[0] - 1, grid[1] - 1), grid=Grid(shape=grid)
        )
        for _ in range(sdk.max_moves * 2):
            if sdk.evaluate_terminal(state) is not None:
                break
            state, _ = controller.execute_single_turn_cycle(state, "ladder", "I edge along")
        rows, cols = grid
        assert 0 <= state.cop_pos[0] < rows and 0 <= state.cop_pos[1] < cols
        assert 0 <= state.thief_pos[0] < rows and 0 <= state.thief_pos[1] < cols
        assert controller._strategy.q.sum() != 0.0  # Q-table accumulated weights

    asyncio.run(_probe_servers())


def test_burner_loopback_dry_run() -> None:
    """Locked production still allows a byte-identical burner handshake."""
    gatekeeper = mock.Mock()
    gatekeeper.execute = mock.Mock(return_value={"id": "loop-1", "status": "SENT"})
    reporter = GmailApiReporter(
        guard=SubmissionSafetyGuard(locked=True), gatekeeper=gatekeeper, service=None
    )
    state = DecPomdpGameState(
        cop_pos=(0, 0), thief_pos=(4, 4), grid=Grid(shape=(5, 5), barriers=frozenset({(1, 1)}))
    )

    first = reporter.dispatch_game_report(state, "mcp.marl.telemetry@gmail.com")
    second = reporter.dispatch_game_report(state, "mcp.marl.telemetry@gmail.com")
    assert first["report_type"] == "internal_game"
    assert len(first["agreement_sha256"]) == 64
    assert first["agreement_sha256"] == second["agreement_sha256"]  # byte-identical
