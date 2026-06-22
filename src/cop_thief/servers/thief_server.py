"""ThiefServer — the Thief agent's FastMCP server."""

from __future__ import annotations

from ..sdk import CopThiefSDK
from .base_server import BaseMCPServer


class ThiefServer(BaseMCPServer):
    """Exposes the Thief agent's tools over MCP (no barrier capability)."""

    def __init__(self, sdk: CopThiefSDK | None = None, token: str | None = None) -> None:
        super().__init__("thief", sdk=sdk, name="thief-server", token=token)
