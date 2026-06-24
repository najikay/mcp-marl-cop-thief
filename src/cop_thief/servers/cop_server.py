"""Cop FastMCP server: receives the Thief's natural-language prose.

Tools are thin wrappers over module-level handlers (the real, directly-testable
logic). All business logic is delegated to :class:`CopThiefSDK`; the server
holds none of its own (Guidelines §5.2).
"""

from __future__ import annotations

from fastmcp import FastMCP

from cop_thief.domain.constants import AgentRole
from cop_thief.sdk import AdversarialHijackDetectedError, CopThiefSDK
from cop_thief.servers.auth import SecurityMiddleware
from cop_thief.servers.tools.move_tool import resolve_move


def handle_thief_prose(
    sdk: CopThiefSDK, security: SecurityMiddleware, prose_payload: str, auth_token: str
) -> str:
    """Authenticate, screen for injection, then return the Cop's reply prose.

    On a detected hijack attempt the Cop intercepts and returns its retaliatory
    counter-strike instead of processing the (malicious) message.
    """
    security.validate(auth_token, AgentRole.COP)
    try:
        sdk.inspect_payload(prose_payload, AgentRole.THIEF)
    except AdversarialHijackDetectedError:
        return sdk.craft_cop_counter_strike()
    return sdk.resolve_prose(prose_payload, AgentRole.COP)


def cop_public_telemetry(sdk: CopThiefSDK) -> dict:
    """Return the Cop's sanitized public telemetry (no strategy weights)."""
    return sdk.public_telemetry()


def create_cop_server(
    sdk: CopThiefSDK | None = None, security: SecurityMiddleware | None = None
) -> FastMCP:
    """Build and return the Cop FastMCP server with its tools registered."""
    sdk = sdk or CopThiefSDK()
    security = security or SecurityMiddleware()
    # NOTE: fastmcp>=2.14 removed the `dependencies` constructor kwarg.
    mcp: FastMCP = FastMCP("CopServer")

    @mcp.tool
    def transmit_thief_prose(prose_payload: str, auth_token: str) -> str:
        """Receive the Thief's prose; counter-strike on injection, else reply."""
        return handle_thief_prose(sdk, security, prose_payload, auth_token)

    @mcp.tool
    def get_cop_public_telemetry() -> dict:
        """Return sanitized agreement-view telemetry (no strategy weights)."""
        return cop_public_telemetry(sdk)

    @mcp.tool
    def request_move(observation: dict, auth_token: str) -> str:
        """A challenger requests the Cop's next move (treaty prose) for a board."""
        security.validate(auth_token, AgentRole.COP)
        return resolve_move({**observation, "role": "cop"})

    return mcp
