"""Challenger transport: fetch a move from a partner MCP server over MCP-SSE.

A *challenger* connects to another team's public MCP endpoint (or, in mirror
mode, our own local ``/sse`` endpoint) and calls its ``request_move`` tool,
receiving the next move as treaty prose. ``fastmcp.Client`` accepts either a live
URL or an in-memory ``FastMCP`` server, so the **same** code path is exercised by
the unit tests (in-memory) and by the live cross-host run (SSE over the tunnel).
"""

from __future__ import annotations

import asyncio

from fastmcp import Client

_MOVE_TOOL = "request_move"


async def fetch_remote_move(
    target, observation: dict, auth_token: str, tool_name: str = _MOVE_TOOL
) -> str:
    """Call the partner's move tool once and return its treaty prose.

    ``target`` is anything ``fastmcp.Client`` accepts — a URL string for a live
    partner, or an in-memory ``FastMCP`` server object for tests. ``tool_name`` is
    configurable so we can call an opponent whose move tool is named differently.
    """
    async with Client(target) as client:
        result = await client.call_tool(
            tool_name, {"observation": observation, "auth_token": auth_token}
        )
    return str(getattr(result, "data", result))


async def list_remote_tools(target) -> list[dict]:
    """Discover an opponent's MCP tools and their argument names (interop probe)."""
    async with Client(target) as client:
        tools = await client.list_tools()
    return [
        {"name": t.name, "args": list((getattr(t, "inputSchema", {}) or {}).get("properties") or {})}
        for t in tools
    ]


class RemoteMoveClient:
    """Sync provider adapter: ``(observation) -> prose`` via a partner MCP server."""

    def __init__(self, target, auth_token: str, tool_name: str = _MOVE_TOOL) -> None:
        """Bind the MCP ``target`` (URL or in-memory server), token and move-tool name."""
        self._target = target
        self._token = auth_token
        self._tool = tool_name

    def __call__(self, observation: dict) -> str:
        """Fetch one remote move synchronously (its own event loop per call)."""
        return asyncio.run(fetch_remote_move(self._target, observation, self._token, self._tool))
