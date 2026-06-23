"""TDD unit test: the dual MCP host configures both Uvicorn servers correctly."""

from __future__ import annotations

import uvicorn

from cop_thief.infra.network.dual_mcp_host import build_servers


def test_build_servers_binds_cop_and_thief_ports() -> None:
    """Cop binds 127.0.0.1:8001 and Thief 127.0.0.1:8002, both at warning level."""
    cop, thief = build_servers()

    assert isinstance(cop, uvicorn.Server)
    assert isinstance(thief, uvicorn.Server)
    assert (cop.config.host, cop.config.port) == ("127.0.0.1", 8001)
    assert (thief.config.host, thief.config.port) == ("127.0.0.1", 8002)
    assert cop.config.log_level == "warning"
    assert thief.config.log_level == "warning"
    assert cop.config.app is not thief.config.app  # two distinct ASGI apps
