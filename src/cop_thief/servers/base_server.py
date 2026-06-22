"""BaseMCPServer — common FastMCP wiring for the Cop and Thief servers.

Registers the four contract tools (see ``docs/BONUS.md`` §2), each delegating to
an :class:`AgentSession` (and thus the SDK). Cop and Thief subclass this and only
differ in their role. The blocking ``run`` is excluded from coverage.
"""

from __future__ import annotations

import os

from fastmcp import FastMCP

from ..sdk import CopThiefSDK
from .session import AgentSession


class BaseMCPServer:
    """A role-bound FastMCP server exposing the agent tool contract."""

    def __init__(
        self,
        role: str,
        sdk: CopThiefSDK | None = None,
        name: str | None = None,
        token: str | None = None,
    ) -> None:
        self.role = role
        self._sdk = sdk or CopThiefSDK(partial_observability=True)
        self._session = AgentSession(self._sdk, role)
        self._token = token or os.environ.get("MCP_TOKEN")
        self.app = FastMCP(name or f"{role}-server")
        self._register()

    def authorized(self, token: str | None) -> bool:
        """True when no token is configured, or the supplied token matches."""
        return self._token is None or token == self._token

    def start_sub_game(self, sub_game_id: str, self_start: list[int]) -> dict:
        """Reset the agent at its orchestrator-assigned start cell."""
        self._session.start((self_start[0], self_start[1]))
        return {"ok": True, "sub_game_id": sub_game_id}

    def receive_message(self, sub_game_id: str, text: str) -> dict:
        """Accept an opponent's free-NL message (updates the belief)."""
        self._session.receive(text)
        return {"ok": True}

    def propose_action(self, sub_game_id: str) -> dict:
        """Return the agent's move and its outgoing free-NL message."""
        return self._session.propose()

    def agree_on_report(self, report: dict) -> dict:
        """Mutual-agreement handshake on a final report."""
        return {"agree": bool(report.get("mutual_agreement", False))}

    def _register(self) -> None:
        self.app.tool(self.start_sub_game)
        self.app.tool(self.receive_message)
        self.app.tool(self.propose_action)
        self.app.tool(self.agree_on_report)

    def run(self, host: str = "127.0.0.1", port: int = 8000) -> None:  # pragma: no cover
        """Serve over HTTP (blocking); used at deploy time, not in tests."""
        self.app.run(transport="http", host=host, port=port)
