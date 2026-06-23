# PRD — Token-Budget Tracking

| Field | Value |
|-------|-------|
| Mechanism | Estimate & accumulate LLM token usage / cost |
| Implements | PRD §N-06 (cost), README §9 (token-cost analysis) |
| Code | [`infra/token_tracker.py`](../src/cop_thief/infra/token_tracker.py), [`infra/llm_client.py`](../src/cop_thief/infra/llm_client.py) (`MeteredLLMClient`) |
| Version | 1.0.0 |

## 1. Purpose
The brief asks for a token-cost analysis and cost-aware operation. Because chase
messages are short and frequent, a lightweight budget tracker lets us report how
many tokens a game consumes and estimate its monetary cost.

## 2. Requirements
| ID | Requirement |
|----|-------------|
| T-1 | Count LLM calls and input/output tokens across a run. |
| T-2 | Real providers report exact usage; offline/mock runs **estimate** (~4 chars/token). |
| T-3 | Convert accumulated tokens to a USD estimate at configurable per-1k rates. |
| T-4 | Tracking is transparent — it wraps the LLM client without changing call sites. |
| T-5 | Usage is exposed as a JSON-friendly snapshot for reports/notebooks. |

## 3. Design
- **`TokenTracker`** — accumulates `calls`, `input_tokens`, `output_tokens`;
  `total_tokens`, `estimated_cost(usd_per_1k_input, usd_per_1k_output)`, `usage()`.
- **`estimate_tokens(text)`** — `max(1, len(text)//4)` for offline budgeting.
- **`MeteredLLMClient(inner)`** — decorates any `LLMClient`, recording estimated
  input/output tokens on every `complete()`; exposes `usage()`.
- **`SDK`** wraps its LLM in `MeteredLLMClient`; `SDK.token_usage()` returns the
  snapshot, so a game's token footprint is queryable after play.

## 4. Acceptance criteria
- `estimate_tokens` is length-based with a floor of 1 (`test_token_tracker`).
- The tracker accumulates and totals correctly; cost uses the supplied rates.
- A metered client records one entry per `complete()` call.
- After a partial-observability game, `SDK.token_usage()["calls"] > 0`.
