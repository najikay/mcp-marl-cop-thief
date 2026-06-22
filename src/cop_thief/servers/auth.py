"""Token-based security middleware for the public MCP servers.

Token *names* are read from config (``servers.cop.auth_env_var`` /
``servers.thief.auth_env_var`` -> ``COP_MCP_TOKEN`` / ``THIEF_MCP_TOKEN``); the
secret *values* are read from the environment. Validation uses
``hmac.compare_digest`` to resist timing attacks. Tokens are revocable by
rotating the environment value (Guidelines / PRD §N-02).
"""

from __future__ import annotations

import hmac
import os
from collections.abc import Callable

from cop_thief.config import get_config_manager
from cop_thief.domain.constants import AgentRole


class SecurityError(RuntimeError):
    """Raised when an MCP request presents a missing or invalid auth token."""


class SecurityMiddleware:
    """Validate per-role bearer tokens for inbound MCP tool calls."""

    def __init__(
        self,
        config_manager=None,
        get_env: Callable[..., str] = os.environ.get,
    ) -> None:
        """Resolve the configured token env-var names for each role."""
        cfg = config_manager or get_config_manager()
        servers = cfg.setup.servers
        self._env = get_env
        self._token_env = {
            AgentRole.COP: servers["cop"].auth_env_var,
            AgentRole.THIEF: servers["thief"].auth_env_var,
        }

    def validate(self, token: str, role: AgentRole) -> None:
        """Constant-time validate ``token`` for ``role``; raise on mismatch.

        Edge case: an empty/unset expected token always rejects (fail-closed).
        """
        expected = self._env(self._token_env[role], "")
        if not expected or not hmac.compare_digest(str(token), str(expected)):
            raise SecurityError(f"Unauthorized {role.value} MCP request.")
