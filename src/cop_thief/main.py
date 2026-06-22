"""CLI entrypoint: run a full game and print the internal JSON report.

Usage (always via uv)::

    uv run cop-thief
    uv run cop-thief --config config/setup.json --group-name Team-Alpha
"""

from __future__ import annotations

import argparse
from pathlib import Path

from .config import ConfigManager
from .domain.agents import CopAgent, ThiefAgent
from .domain.reporting import InternalReport
from .domain.strategy import HeuristicStrategy
from .orchestrator import GameLoopController


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a Cop & Thief game.")
    parser.add_argument("--config", default=None, help="path to setup.json")
    parser.add_argument("--group-name", default="Team-Alpha")
    parser.add_argument("--github-repo", default="https://github.com/example/marl-cop-thief")
    parser.add_argument("--cop-url", default="http://localhost:8001")
    parser.add_argument("--thief-url", default="http://localhost:8002")
    parser.add_argument("--out", default=None, help="optional path to write the JSON report")
    return parser.parse_args()


def main() -> None:
    """Load config, play a full game, and emit the internal JSON report."""
    args = _parse_args()
    config = ConfigManager(args.config).load()
    cop = CopAgent(HeuristicStrategy())
    thief = ThiefAgent(HeuristicStrategy())
    result = GameLoopController(config, cop, thief).play_game()
    report = InternalReport(
        group_name=args.group_name,
        github_repo=args.github_repo,
        cop_mcp_url=args.cop_url,
        thief_mcp_url=args.thief_url,
        result=result,
    )
    rows, cols = config.grid_size
    print(f"# {rows}x{cols} game - cop {result.cop_total} / thief {result.thief_total}")
    payload = report.to_json()
    print(payload)
    if args.out:
        Path(args.out).write_text(payload, encoding="utf-8")
        print(f"# report written to {args.out}")


if __name__ == "__main__":
    main()
