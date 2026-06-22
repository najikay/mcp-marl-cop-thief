"""CopServer — the Cop agent's FastMCP server."""

from __future__ import annotations

from ..sdk import CopThiefSDK
from .base_server import BaseMCPServer


class CopServer(BaseMCPServer):
    """Exposes the Cop agent's tools over MCP."""

    def __init__(self, sdk: CopThiefSDK | None = None, token: str | None = None) -> None:
        super().__init__("cop", sdk=sdk, name="cop-server", token=token)
