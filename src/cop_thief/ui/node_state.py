"""Thread-safe live node status for the control panel (servers, tunnels, game).

A single process-wide :data:`STATE` is updated by the boot sequence (servers up,
tunnel URLs captured) and by the challenge worker (game status), and read by the
``/api/status`` endpoint. Tokens are read from the environment at snapshot time so
the panel can show the exact values to share with an opponent.
"""

from __future__ import annotations

import os
import threading


class NodeState:
    """Mutable, lock-guarded snapshot of the node's live status."""

    def __init__(self) -> None:
        """Start with everything down/idle until the boot sequence reports in."""
        self._lock = threading.Lock()
        self.servers_up = False
        self.tunnels_up = False
        self.cop_url = ""
        self.thief_url = ""
        self.game_status = "idle"
        self.last_result: dict | None = None

    def set_servers_up(self) -> None:
        """Mark both MCP servers as listening."""
        with self._lock:
            self.servers_up = True

    def set_tunnels(self, cop_url: str, thief_url: str) -> None:
        """Record the captured public ``/mcp/`` URLs and mark tunnels live."""
        with self._lock:
            self.tunnels_up = True
            self.cop_url, self.thief_url = cop_url, thief_url

    def set_game(self, status: str, result: dict | None = None) -> None:
        """Update the game phase (idle | playing | done) and optional last result."""
        with self._lock:
            self.game_status = status
            if result is not None:
                self.last_result = result

    def snapshot(self) -> dict:
        """Return a JSON-serializable copy of the current status (tokens from env)."""
        with self._lock:
            return {
                "servers_up": self.servers_up,
                "tunnels_up": self.tunnels_up,
                "cop_url": self.cop_url,
                "thief_url": self.thief_url,
                "cop_token": os.environ.get("COP_MCP_TOKEN", ""),
                "thief_token": os.environ.get("THIEF_MCP_TOKEN", ""),
                "game_status": self.game_status,
                "last_result": self.last_result,
            }


STATE = NodeState()
