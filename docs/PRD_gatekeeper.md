# PRD — API Gatekeeper

| Field | Value |
|-------|-------|
| Mechanism | Centralized gatekeeper for all external (LLM + Gmail) calls |
| Implements | PRD §F-11, §E4, PLAN §5 |
| Code | [`infra/gatekeeper.py`](../src/cop_thief/infra/gatekeeper.py), [`rate_limiter.py`](../src/cop_thief/infra/rate_limiter.py), [`retry.py`](../src/cop_thief/infra/retry.py), [`logger.py`](../src/cop_thief/infra/logger.py) |
| Config | [`config/rate_limits.json`](../config/rate_limits.json) → [`config/rate_limits.py`](../src/cop_thief/config/rate_limits.py) |
| Version | 1.0.0 |

## 1. Purpose
Every call that leaves the process (LLM completions, Gmail sends) must pass
through **one** chokepoint so rate limits, retries, back-pressure and monitoring
are applied uniformly and no caller duplicates `try/except` IO logic.

## 2. Requirements
| ID | Requirement |
|----|-------------|
| G-1 | 100% of LLM/Gmail calls routed via `ApiGatekeeper.execute(service, func)`. |
| G-2 | Per-service limits (`default`, `llm`, `gmail`) read from versioned JSON; never hardcoded. |
| G-3 | Over-budget calls raise a controlled `BackpressureError` — **never crash**. |
| G-4 | Transient failures retried with bounded backoff; permanent failures surface at once. |
| G-5 | Every call emits a structured log event; secret-looking fields are redacted. |

## 3. Design
- **`RateLimiter`** — sliding per-minute window counters per service, with an
  **injectable clock** so tests are deterministic (no real waiting).
- **`RetryPolicy`** — retries only `TransientError` up to `max_retries`, sleeping
  `retry_after_seconds` (injectable sleeper); `PermanentError` is never retried.
- **`ApiGatekeeper.execute(service, func)`** — checks the limiter (→ `BackpressureError`
  when over budget), then runs `func` under the retry policy, logging each attempt.
- **`StructuredLogger`** — records `(event, fields)` to an in-memory buffer and the
  stdlib logger; redacts keys containing `key|token|secret|password`.

```
caller ─▶ execute(service, func)
            ├─ RateLimiter.allow(service)? ──no──▶ BackpressureError (logged)
            └─yes─▶ RetryPolicy.run(func) ──▶ result (logged)
```

## 4. Failure taxonomy
| Failure | Response |
|---------|----------|
| Rate limit reached | `BackpressureError` (caller slows down / degrades) |
| Transient 5xx / timeout (`TransientError`) | retry with backoff up to `max_retries` |
| Permanent error | surface immediately, no retry |
| LLM rate-limited mid-game | parser catches it and falls back to the offline heuristic |

## 5. Acceptance criteria
- Under-limit call passes through and is logged (`test_gatekeeper`).
- At-limit call raises `BackpressureError`; window reset re-allows (`test_rate_limiter`).
- Retry succeeds on the 2nd attempt; exhaustion re-raises (`test_retry`).
- No source path performs an external call outside the gatekeeper (design review).
