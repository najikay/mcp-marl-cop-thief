"""LLMClient — one interface over cloud / Ollama / offline-mock providers.

The provider is selected from the ``LLM_PROVIDER`` env var (PRD §N-03). The
default is the deterministic :class:`MockLLMClient`, so the whole pipeline runs
offline with no API key until a real provider is wired in.
"""

from __future__ import annotations

import os
from abc import ABC, abstractmethod

from .token_tracker import TokenTracker, estimate_tokens


class LLMClient(ABC):
    """A text-in / text-out language-model client behind the gatekeeper."""

    @abstractmethod
    def complete(self, prompt: str) -> str:
        """Return the model's completion for ``prompt``."""
        raise NotImplementedError


class MeteredLLMClient(LLMClient):
    """Wrap any client to count token usage on every completion."""

    def __init__(self, inner: LLMClient, tracker: TokenTracker | None = None) -> None:
        self._inner = inner
        self._tracker = tracker or TokenTracker()

    def complete(self, prompt: str) -> str:
        """Delegate, recording estimated input/output tokens for the call."""
        output = self._inner.complete(prompt)
        self._tracker.record(estimate_tokens(prompt), estimate_tokens(output))
        return output

    def usage(self) -> dict:
        """Return the accumulated token-usage snapshot."""
        return self._tracker.usage()


class MockLLMClient(LLMClient):
    """Deterministic offline stand-in: echoes a trimmed, marked response.

    Good enough to exercise the orchestration plumbing without a network call;
    real adapters (cloud, Ollama) replace it once a provider is chosen.
    """

    def complete(self, prompt: str) -> str:
        """Return a deterministic, prompt-derived reply."""
        return f"[mock-llm] {prompt.strip()[:200]}"


def make_llm_client(provider: str | None = None) -> LLMClient:
    """Factory: pick a provider from the argument or ``LLM_PROVIDER`` env var."""
    choice = (provider or os.environ.get("LLM_PROVIDER", "mock")).lower()
    if choice in ("mock", ""):
        return MockLLMClient()
    if choice in ("cloud", "ollama", "hybrid"):
        raise NotImplementedError(
            f"LLM provider '{choice}' not wired yet; set LLM_PROVIDER=mock for now"
        )
    raise ValueError(f"unknown LLM provider: {choice}")
