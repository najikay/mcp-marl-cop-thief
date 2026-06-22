"""MCPAgentClient — async wrapper around a FastMCP client for one agent server.

The ``target`` may be a public URL (real deployment) or a FastMCP app object
(in-memory transport, used by tests) — FastMCP's ``Client`` accepts both, so the
same orchestrator drives local and cloud servers unchanged.
"""

from __future__ import annotations

from fastmcp import Client


class MCPAgentClient:
    """Call one agent server's contract tools over MCP."""

    def __init__(self, target) -> None:
        self._client = Client(target)

    async def __aenter__(self) -> MCPAgentClient:
        await self._client.__aenter__()
        return self

    async def __aexit__(self, *exc) -> None:
        await self._client.__aexit__(*exc)

    async def start_sub_game(self, sub_game_id: str, self_start: list[int]) -> None:
        """Tell the server its own start cell for a new sub-game."""
        await self._client.call_tool(
            "start_sub_game", {"sub_game_id": sub_game_id, "self_start": self_start}
        )

    async def receive_message(self, sub_game_id: str, text: str) -> None:
        """Relay the opponent's free-NL message to this server."""
        await self._client.call_tool(
            "receive_message", {"sub_game_id": sub_game_id, "text": text}
        )

    async def propose_action(self, sub_game_id: str) -> dict:
        """Ask the server for its move and outgoing message."""
        result = await self._client.call_tool("propose_action", {"sub_game_id": sub_game_id})
        return result.data

    async def agree_on_report(self, report: dict) -> bool:
        """Run the mutual-agreement handshake; return whether it agrees."""
        result = await self._client.call_tool("agree_on_report", {"report": report})
        return bool(result.data.get("agree", False))
