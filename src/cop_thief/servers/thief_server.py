"""Thief FastMCP server: receives the Cop's natural-language prose.

Symmetrical to ``cop_server.py``. May optionally append a phantom-hazard claim
to its evasive reply when ``phantom_target`` is configured (in-game deception
for the consensual inter-group competition).
"""

from __future__ import annotations

from fastmcp import FastMCP

from cop_thief.domain.constants import AgentRole
from cop_thief.sdk import AdversarialHijackDetectedError, CopThiefSDK
from cop_thief.servers.auth import SecurityMiddleware


def handle_cop_prose(
    sdk: CopThiefSDK,
    security: SecurityMiddleware,
    prose_payload: str,
    auth_token: str,
    phantom_target: tuple[int, int] | None = None,
) -> str:
    """Authenticate, screen for injection, then return the Thief's reply prose.

    On a detected hijack the Thief returns its counter-strike. Otherwise it
    replies with evasive prose, optionally appending a phantom-hazard claim.
    """
    security.validate(auth_token, AgentRole.THIEF)
    try:
        sdk.inspect_payload(prose_payload, AgentRole.COP)
    except AdversarialHijackDetectedError:
        return sdk.craft_thief_counter_strike()
    reply = sdk.resolve_prose(prose_payload, AgentRole.THIEF)
    if phantom_target is not None:
        reply = f"{reply} {sdk.craft_phantom_hazard_claim(phantom_target)}"
    return reply


def thief_public_telemetry(sdk: CopThiefSDK) -> dict:
    """Return the Thief's sanitized public telemetry (no strategy weights)."""
    return sdk.public_telemetry()


def create_thief_server(
    sdk: CopThiefSDK | None = None, security: SecurityMiddleware | None = None
) -> FastMCP:
    """Build and return the Thief FastMCP server with its tools registered."""
    sdk = sdk or CopThiefSDK()
    security = security or SecurityMiddleware()
    # NOTE: fastmcp>=2.14 removed the `dependencies` constructor kwarg.
    mcp: FastMCP = FastMCP("ThiefServer")

    @mcp.tool
    def transmit_cop_prose(prose_payload: str, auth_token: str) -> str:
        """Receive the Cop's prose; counter-strike on injection, else evade."""
        return handle_cop_prose(sdk, security, prose_payload, auth_token)

    @mcp.tool
    def get_thief_public_telemetry() -> dict:
        """Return sanitized agreement-view telemetry (no strategy weights)."""
        return thief_public_telemetry(sdk)

    return mcp
