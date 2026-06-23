"""Master CLI & GUI orchestrator for marl-cop-thief.

Modes: headless (autonomous series), gui (live tkinter observer + asyncio
worker), sanity_check (grid ladder). ``--dry-run`` (default True) forces the
report recipient to the burner sandbox to prevent accidental live submissions.
"""

from __future__ import annotations

import argparse
import asyncio
import threading

from cop_thief.config import get_config_manager
from cop_thief.domain.constants import SubGameOutcome
from cop_thief.domain.grid import Grid
from cop_thief.domain.state import DecPomdpGameState
from cop_thief.orchestrator import GameLoopController
from cop_thief.reporting import GmailApiReporter
from cop_thief.sdk import CopThiefSDK

_GRIDS = {"2x2": (2, 2), "3x3": (3, 3), "4x4": (4, 4), "5x5": (5, 5)}


def build_parser() -> argparse.ArgumentParser:
    """Build the CLI argument parser."""
    parser = argparse.ArgumentParser(prog="cop-thief", description="Dec-POMDP Cop & Thief pursuit")
    parser.add_argument("--mode", choices=["headless", "gui", "sanity_check"], default="headless")
    parser.add_argument("--grid", choices=list(_GRIDS), default="5x5")
    parser.add_argument("--dry-run", dest="dry_run", action="store_true", default=True)
    parser.add_argument("--no-dry-run", dest="dry_run", action="store_false")
    return parser


def _recipient(dry_run: bool) -> str:
    """Resolve the report recipient (burner when dry-run, else examiner)."""
    reporting = get_config_manager().get_setup().reporting
    return reporting.burner_email if dry_run else reporting.examiner_email


def _initial_state(grid: tuple[int, int]) -> DecPomdpGameState:
    """Build a corner-start initial state for the given grid."""
    return DecPomdpGameState(
        cop_pos=(0, 0), thief_pos=(grid[0] - 1, grid[1] - 1), grid=Grid(shape=grid)
    )


def _safe_report(state: DecPomdpGameState, recipient: str) -> None:
    """Dispatch the end-game report, never crashing the app on failure."""
    try:
        reporter = GmailApiReporter()
        reporter.bootstrap_oauth()
        result = reporter.dispatch_game_report(state, recipient)
        print(f"Report dispatched to {recipient}: {result.get('agreement_sha256')}")
    except (OSError, RuntimeError, ValueError) as exc:
        print(f"Report skipped ({type(exc).__name__}): {exc}")


def run_headless(grid: tuple[int, int], recipient: str) -> SubGameOutcome:
    """Run one autonomous sub-game series headlessly, then report."""
    controller = GameLoopController()
    outcome = controller.run_simulated_sub_game("mock_partner_node")
    _safe_report(_initial_state(grid), recipient)
    print(f"Headless sub-game outcome: {outcome.value}")
    return outcome


def run_sanity(recipient: str) -> None:
    """Run the 2x2 -> 5x5 sanity ladder."""
    for label in _GRIDS:
        controller = GameLoopController()
        outcome = controller.run_simulated_sub_game("sanity")
        print(f"[sanity {label}] outcome: {outcome.value}")


def run_gui(grid: tuple[int, int], recipient: str) -> None:
    """Boot the tkinter observer with an asyncio pursuit worker."""
    from cop_thief.gui import ObserverGUI

    sdk = CopThiefSDK()
    sdk.initialize_match()
    gui = ObserverGUI(grid_size=grid[0])
    controller = GameLoopController(sdk=sdk)

    async def worker() -> None:
        state = _initial_state(grid)
        for _ in range(sdk.max_moves * 2):
            if sdk.evaluate_terminal(state) is not None:
                break
            state, prose = controller.execute_single_turn_cycle(state, "mock", "I edge along")
            gui.dispatch_update(state, prose, state.turn_role)
            await asyncio.sleep(0.05)
        _safe_report(state, recipient)

    threading.Thread(target=lambda: asyncio.run(worker()), daemon=True).start()
    gui.root.mainloop()


def main(argv: list[str] | None = None) -> None:
    """CLI entrypoint: dispatch by mode."""
    args = build_parser().parse_args(argv)
    grid = _GRIDS[args.grid]
    recipient = _recipient(args.dry_run)
    if args.mode == "gui":
        run_gui(grid, recipient)
    elif args.mode == "sanity_check":
        run_sanity(recipient)
    else:
        run_headless(grid, recipient)


if __name__ == "__main__":
    main()
