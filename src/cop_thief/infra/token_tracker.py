"""TokenTracker — estimate and accumulate LLM token usage and cost.

The brief asks for a token-cost analysis (PRD §N-06, README §9). Real providers
return exact usage; offline/mock runs estimate ~4 characters per token. The
tracker accumulates input/output tokens and converts to an optional USD cost.
"""

from __future__ import annotations

from dataclasses import dataclass

_CHARS_PER_TOKEN = 4


def estimate_tokens(text: str) -> int:
    """Rough token estimate (~4 chars/token) for offline budgeting."""
    return max(1, len(text) // _CHARS_PER_TOKEN)


@dataclass
class TokenTracker:
    """Accumulate LLM call counts and input/output token estimates."""

    calls: int = 0
    input_tokens: int = 0
    output_tokens: int = 0

    def record(self, input_tokens: int, output_tokens: int) -> None:
        """Add one call's input/output token counts to the running totals."""
        self.calls += 1
        self.input_tokens += input_tokens
        self.output_tokens += output_tokens

    @property
    def total_tokens(self) -> int:
        """Sum of input and output tokens recorded so far."""
        return self.input_tokens + self.output_tokens

    def estimated_cost(
        self, usd_per_1k_input: float = 0.0, usd_per_1k_output: float = 0.0
    ) -> float:
        """Convert accumulated tokens to a USD estimate at the given rates."""
        return (
            self.input_tokens / 1000 * usd_per_1k_input
            + self.output_tokens / 1000 * usd_per_1k_output
        )

    def usage(self) -> dict:
        """Return a JSON-friendly snapshot of usage so far."""
        return {
            "calls": self.calls,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "total_tokens": self.total_tokens,
        }
