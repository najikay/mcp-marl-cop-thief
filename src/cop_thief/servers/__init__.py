"""Dual FastMCP servers: Cop and Thief natural-language transmission endpoints."""

from cop_thief.servers.auth import SecurityError, SecurityMiddleware
from cop_thief.servers.cop_server import create_cop_server
from cop_thief.servers.thief_server import create_thief_server

__all__ = [
    "create_cop_server",
    "create_thief_server",
    "SecurityMiddleware",
    "SecurityError",
]
