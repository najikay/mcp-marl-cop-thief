"""Thread-safe token-usage accumulator with atomic persistence.

Records every LLM turn and computes real-time cost economics. Persistence is
atomic (temp file + ``os.replace``) so the ledger is never left half-written.

NOTE: ``LEDGER_RATES`` is an explicit per-provider pricing ledger (per the batch
mandate). Strictly, Guidelines §7.2 would place such values in config; these are
isolated here as a single named constant and can be promoted to ``setup.json``
without touching call sites.
"""

from __future__ import annotations

import json
import threading
from pathlib import Path

LEDGER_RATES: dict[str, dict[str, float]] = {
    "DEEPSEEK": {"input": 0.15, "output": 0.60},
    "ANTHROPIC": {"input": 3.00, "output": 15.00},
}


class TokenTracker:
    """Accumulate per-turn token usage and expose live cost economics."""

    def __init__(self, usage_file: str | Path = "data/token_usage.json") -> None:
        """Initialise the tracker, loading any existing ledger from disk."""
        self._path = Path(usage_file)
        self._lock = threading.Lock()
        self._turns: list[dict] = self._load()

    def _load(self) -> list[dict]:
        """Read previously persisted turns, tolerating a missing/empty file."""
        if not self._path.exists():
            return []
        try:
            return json.loads(self._path.read_text(encoding="utf-8")).get("turns", [])
        except (json.JSONDecodeError, OSError):
            return []

    def _flush(self) -> None:
        """Persist the ledger atomically (temp file then replace)."""
        self._path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self._path.with_suffix(".tmp")
        tmp.write_text(
            json.dumps({"version": "1.00", "turns": self._turns}, indent=2),
            encoding="utf-8",
        )
        tmp.replace(self._path)

    def log_turn(
        self, provider: str, model: str, input_tokens: int, output_tokens: int
    ) -> None:
        """Append one LLM turn's usage and persist atomically (thread-safe)."""
        with self._lock:
            self._turns.append(
                {
                    "provider": provider,
                    "model": model,
                    "input_tokens": max(0, int(input_tokens)),
                    "output_tokens": max(0, int(output_tokens)),
                }
            )
            self._flush()

    def get_current_economics(self) -> dict:
        """Return accumulated tokens and exact USD cost across all turns."""
        total_in = total_out = 0
        cost = 0.0
        for turn in self._turns:
            rate = LEDGER_RATES.get(turn["provider"], LEDGER_RATES["DEEPSEEK"])
            total_in += turn["input_tokens"]
            total_out += turn["output_tokens"]
            cost += turn["input_tokens"] / 1e6 * rate["input"]
            cost += turn["output_tokens"] / 1e6 * rate["output"]
        return {
            "input_accumulated": total_in,
            "output_accumulated": total_out,
            "estimated_cost_usd": round(cost, 6),
            "turns": len(self._turns),
        }
