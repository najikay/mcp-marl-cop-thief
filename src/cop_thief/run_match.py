"""CLI: drive a full game against two running MCP servers (local or cloud).

Excluded from coverage (network entrypoint). Usage::

    uv run cop-thief-match --cop-url http://127.0.0.1:8001/mcp \
                           --thief-url http://127.0.0.1:8002/mcp
"""

from __future__ import annotations

import argparse
from pathlib import Path

from .sdk import CopThiefSDK


def _parse_args() -> argparse.Namespace:  # pragma: no cover
    parser = argparse.ArgumentParser(description="Run a game across two MCP servers.")
    parser.add_argument("--config", default=None)
    parser.add_argument("--cop-url", required=True, help="Cop server MCP URL")
    parser.add_argument("--thief-url", required=True, help="Thief server MCP URL")
    parser.add_argument("--group-name", default="Team-Alpha")
    parser.add_argument("--github-repo", default="https://github.com/example/marl-cop-thief")
    parser.add_argument("--out", default=None)
    return parser.parse_args()


def main() -> None:  # pragma: no cover
    """Play a remote game and print the internal JSON report."""
    args = _parse_args()
    sdk = CopThiefSDK.from_config_path(args.config)
    result = sdk.play_remote_game(args.cop_url, args.thief_url)
    report = sdk.build_internal_report(
        result, args.group_name, args.github_repo, args.cop_url, args.thief_url
    )
    print(f"# remote game - cop {result.cop_total} / thief {result.thief_total}")
    payload = report.to_json()
    print(payload)
    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(payload, encoding="utf-8")


if __name__ == "__main__":
    main()
