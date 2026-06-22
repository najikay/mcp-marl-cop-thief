"""CLI entrypoint: run a full game and print the internal JSON report.

Imports **only** the SDK (no domain/infra imports) to honour the single-entrypoint
boundary (PRD §E3). Usage (always via uv)::

    uv run cop-thief
    uv run cop-thief --config config/setup.json --group-name Team-Alpha
"""

from __future__ import annotations

import argparse
from pathlib import Path

from .sdk import CopThiefSDK


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
    sdk = CopThiefSDK.from_config_path(args.config)
    config = sdk.config
    result = sdk.play_game()
    report = sdk.build_internal_report(
        result,
        group_name=args.group_name,
        github_repo=args.github_repo,
        cop_mcp_url=args.cop_url,
        thief_mcp_url=args.thief_url,
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
