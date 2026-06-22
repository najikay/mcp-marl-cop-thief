"""Provider-specific HTTP payload builders and response parsers.

Extracted from ``engine.py`` to honour the 150-line limit. Single concern:
translate a (prompt, system, model) triple into each provider's request shape,
and normalise each provider's response into ``(text, usage)`` where ``usage`` is
``{"input_tokens": int, "output_tokens": int}``.
"""

from __future__ import annotations

ANTHROPIC_VERSION = "2023-06-01"
ANTHROPIC_MAX_TOKENS = 1024


class PayloadBuilderMixin:
    """Mixin of pure, stateless request/response adapters for both providers."""

    @staticmethod
    def headers_deepseek(api_key: str) -> dict:
        """Return DeepSeek (OpenAI-compatible) auth headers."""
        return {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

    @staticmethod
    def headers_anthropic(api_key: str) -> dict:
        """Return Anthropic Messages-API auth headers."""
        return {
            "x-api-key": api_key,
            "anthropic-version": ANTHROPIC_VERSION,
            "Content-Type": "application/json",
        }

    @staticmethod
    def build_deepseek(prompt: str, system_instruction: str, model: str) -> dict:
        """Build a DeepSeek chat-completions request body."""
        return {
            "model": model,
            "messages": [
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": prompt},
            ],
        }

    @staticmethod
    def build_anthropic(prompt: str, system_instruction: str, model: str) -> dict:
        """Build an Anthropic Messages request body."""
        return {
            "model": model,
            "max_tokens": ANTHROPIC_MAX_TOKENS,
            "system": system_instruction,
            "messages": [{"role": "user", "content": prompt}],
        }

    @staticmethod
    def parse_deepseek(data: dict) -> tuple[str, dict]:
        """Normalise a DeepSeek response into ``(text, usage)``."""
        text = data["choices"][0]["message"]["content"]
        raw = data.get("usage", {})
        usage = {
            "input_tokens": int(raw.get("prompt_tokens", 0)),
            "output_tokens": int(raw.get("completion_tokens", 0)),
        }
        return text, usage

    @staticmethod
    def parse_anthropic(data: dict) -> tuple[str, dict]:
        """Normalise an Anthropic response into ``(text, usage)``."""
        text = data["content"][0]["text"]
        raw = data.get("usage", {})
        usage = {
            "input_tokens": int(raw.get("input_tokens", 0)),
            "output_tokens": int(raw.get("output_tokens", 0)),
        }
        return text, usage
