"""Unit tests for MCPAgentClient transport selection (token handling)."""

from __future__ import annotations

from fastmcp.client.transports import StreamableHttpTransport

from cop_thief.orchestrator import MCPAgentClient
from cop_thief.servers import CopServer


def test_url_with_token_builds_http_transport():
    transport = MCPAgentClient._transport("https://cop.example/mcp/", "tok")
    assert isinstance(transport, StreamableHttpTransport)


def test_url_without_token_passes_through():
    assert MCPAgentClient._transport("https://cop.example/mcp/", None) == "https://cop.example/mcp/"


def test_in_memory_app_target_ignores_token():
    app = CopServer().app
    assert MCPAgentClient._transport(app, "tok") is app  # in-memory needs no bearer
