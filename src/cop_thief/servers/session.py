"""AgentSession — per-sub-game state for one MCP agent server.

Tracks only what an agent legitimately knows: its own cell and the belief parsed
from the opponent's free-text messages. All decisions are delegated to the SDK,
so the server holds no business logic (PRD §E3).
"""

from __future__ import annotations


class AgentSession:
    """Holds an agent's own position and belief across one sub-game."""

    def __init__(self, sdk, role: str) -> None:
        self._sdk = sdk
        self._role = role
        self._self_cell: tuple[int, int] = (0, 0)
        self._belief = None

    def start(self, self_start: tuple[int, int]) -> None:
        """Begin a sub-game at the orchestrator-assigned own start cell."""
        self._self_cell = (int(self_start[0]), int(self_start[1]))
        self._belief = None

    def receive(self, text: str) -> None:
        """Ingest an opponent's free-NL message and update the belief."""
        self._belief = self._sdk.parse_message(text)

    def propose(self) -> dict:
        """Decide this turn; advance own cell; return action + outgoing message."""
        result = self._sdk.propose_turn(self._self_cell, self._role, self._belief)
        self._self_cell = tuple(result.pop("next_cell"))
        return result
