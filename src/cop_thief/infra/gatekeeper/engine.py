"""Centralized synchronous HTTP chokepoint for all external LLM traffic.

The gatekeeper enforces FIFO backpressure, performs zero-crash provider
failover (DeepSeek -> Anthropic) using pure ``httpx``, and records token
economics. All payload shaping lives in :class:`PayloadBuilderMixin`.
"""

from __future__ import annotations

import contextlib
import logging
import os
import queue
from collections.abc import Callable

import httpx

from cop_thief.infra.gatekeeper.exceptions import (
    BackpressureOverflowError,
    ProviderUpstreamError,
)
from cop_thief.infra.gatekeeper.payload_builder import PayloadBuilderMixin
from cop_thief.infra.gatekeeper.token_tracker import TokenTracker

logger = logging.getLogger("cop_thief.gatekeeper")

DEEPSEEK_PATH = "/chat/completions"
ANTHROPIC_PATH = "/v1/messages"
_TRANSPORT_ERRORS = (httpx.HTTPStatusError, httpx.RequestError)


class ApiGatekeeper(PayloadBuilderMixin):
    """FIFO-bounded, failover-capable manager for all LLM API calls."""

    def __init__(
        self,
        rate_limits,
        llm_routing,
        token_tracker: TokenTracker | None = None,
        client: httpx.Client | None = None,
        get_env: Callable[..., str] = os.environ.get,
    ) -> None:
        """Wire config-derived limits, routing, transport and telemetry."""
        self._routing = llm_routing
        default = rate_limits.rate_limits.services.get("default")
        self._queue_max = default.queue_max_depth if default else 100
        self._queue: queue.Queue = queue.Queue(maxsize=self._queue_max)
        self._tracker = token_tracker or TokenTracker()
        self._client = client or httpx.Client(timeout=60)
        self._get_env = get_env

    def _acquire(self) -> None:
        """Reserve a FIFO slot; raise on overflow instead of blocking/crashing."""
        try:
            self._queue.put_nowait(1)
        except queue.Full as exc:
            raise BackpressureOverflowError(
                f"Gatekeeper queue full (depth={self._queue_max}); slow the tick."
            ) from exc

    def _release(self) -> None:
        """Release a previously reserved FIFO slot."""
        with contextlib.suppress(queue.Empty):
            self._queue.get_nowait()

    def execute_llm_call(
        self, prompt: str, system_instruction: str, primary_provider: str = "DEEPSEEK"
    ) -> tuple[str, dict]:
        """Execute an LLM call through the gatekeeper, returning ``(text, usage)``."""
        self._acquire()
        try:
            return self._with_failover(prompt, system_instruction)
        finally:
            self._release()

    def _with_failover(self, prompt: str, system: str) -> tuple[str, dict]:
        """Try the primary provider; on transport failure, retry the fallback."""
        try:
            return self._call_deepseek(self._routing.primary, prompt, system)
        except _TRANSPORT_ERRORS as exc:
            logger.warning(
                "Primary LLM failed; failing over to fallback provider.",
                extra={"event": "llm_failover", "error": str(exc)},
            )
            try:
                return self._call_anthropic(self._routing.fallback, prompt, system)
            except _TRANSPORT_ERRORS as exc2:
                raise ProviderUpstreamError("All LLM providers failed.") from exc2

    def _call_deepseek(self, endpoint, prompt: str, system: str) -> tuple[str, dict]:
        """Call DeepSeek's chat-completions endpoint and record usage."""
        url = endpoint.base_url.rstrip("/") + DEEPSEEK_PATH
        headers = self.headers_deepseek(self._get_env(endpoint.api_key_env_var, ""))
        response = self._client.post(
            url, json=self.build_deepseek(prompt, system, endpoint.model), headers=headers
        )
        response.raise_for_status()
        text, usage = self.parse_deepseek(response.json())
        self._tracker.log_turn(endpoint.provider, endpoint.model, **usage)
        return text, {"provider": endpoint.provider, "model": endpoint.model, **usage}

    def _call_anthropic(self, endpoint, prompt: str, system: str) -> tuple[str, dict]:
        """Call Anthropic's messages endpoint and record usage."""
        url = endpoint.base_url.rstrip("/") + ANTHROPIC_PATH
        headers = self.headers_anthropic(self._get_env(endpoint.api_key_env_var, ""))
        response = self._client.post(
            url, json=self.build_anthropic(prompt, system, endpoint.model), headers=headers
        )
        response.raise_for_status()
        text, usage = self.parse_anthropic(response.json())
        self._tracker.log_turn(endpoint.provider, endpoint.model, **usage)
        return text, {"provider": endpoint.provider, "model": endpoint.model, **usage}
