"""CLI launchers for the Cop and Thief MCP servers (excluded from coverage).

Usage (always via uv)::

    uv run cop-server --host 127.0.0.1 --port 8001
    uv run thief-server --port 8002
"""

from __future__ import annotations

import argparse

from .cop_server import CopServer
from .thief_server import ThiefServer


def _args(default_port: int) -> argparse.Namespace:  # pragma: no cover
    parser = argparse.ArgumentParser(description="Run a Cop/Thief MCP server.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=default_port)
    return parser.parse_args()


def run_cop() -> None:  # pragma: no cover
    """Console-script entrypoint: serve the Cop MCP server."""
    args = _args(8001)
    CopServer().run(host=args.host, port=args.port)


def run_thief() -> None:  # pragma: no cover
    """Console-script entrypoint: serve the Thief MCP server."""
    args = _args(8002)
    ThiefServer().run(host=args.host, port=args.port)
