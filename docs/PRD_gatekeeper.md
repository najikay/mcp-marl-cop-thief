# PRD (Per-Mechanism) — API Gatekeeper & Rate-Limiting Engine
## `marl-cop-thief` · Mechanism: Centralized External-Call Chokepoint

| Field | Value |
|-------|-------|
| Mechanism ID | `MECH-GATEKEEPER` |
| Document version | 1.00 |
| Parent docs | [`PRD.md`](./PRD.md) · [`PLAN.md`](./PLAN.md) · [`TODO.md`](./TODO.md) (Task #117, Phase 3) |
| Source modules | `infra/gatekeeper.py`, `infra/rate_limiter.py`, `infra/retry.py`, `infra/queue_monitor.py` |
| Related | [`PRD_token_budget.md`](./PRD_token_budget.md) (TokenTracker delegate) |
| Standard | Dr. Segal *Guidelines v3.00* (§5 API Gatekeeper, §2.3, §11) |
| Status | Draft — approve before implementing Phase 3 |

> **Governing mandate (Guidelines §5.1).** *All* external API calls (LLM clients **and** the Gmail
> API) **must** pass through one centralized gatekeeper. No call may bypass it. The gatekeeper handles
> rate limiting, FIFO queuing, retries, monitoring — and **must never crash on overflow**.

---

## 1. Theoretical & Mathematical Background

### 1.1 The gatekeeper as a bounded queueing system
The gatekeeper is a classic **bounded single-server queue with admission control** (≈ M/M/c/K):
arrivals are API requests, the "server" is the rate-limited external service with `concurrent_max`
parallel slots, and `K = queue_max_depth` is the buffer bound. Admission is governed by token-bucket
rate windows; when the buffer is full, **backpressure** (not loss) is applied.

### 1.2 Token-bucket rate limiting
For each service we maintain windowed counters. A request is admitted iff all windows have headroom:
```
allow(t) ⇔ count_minute(t) < rpm  ∧  count_hour(t) < rph  ∧  in_flight(t) < concurrent_max
```
Windows reset on a sliding/tumbling basis (`requests_per_minute`, `requests_per_hour`). On
`¬allow(t)` the request is **enqueued** (FIFO), never dropped.

### 1.3 Little's Law (capacity sanity)
`L = λ · W` (mean items in system = arrival rate × mean time in system). We size `queue_max_depth`
so that expected wait `W = L/λ` stays within turn-cycle tolerances; exceeding `K` raises backpressure
that throttles `λ` at the source (the orchestrator slows the turn cycle).

### 1.4 Retry with exponential backoff
Transient failures are retried with backoff:
```
delay_k = min( retry_after_seconds · 2^(k-1) , cap ) ,   k = 1 … max_retries
```
Permanent failures (4xx auth/validation) are **not** retried.

---

## 2. Architecture & The `execute()` Chokepoint

### 2.1 Single entrypoint
```python
class ApiGatekeeper:
    """Centralized manager for ALL external API calls (LLM + Gmail)."""
    def __init__(self, config: RateLimitConfig, token_tracker: "TokenTracker"): ...
    def execute(self, api_call, *args, service: str = "default", **kwargs): ...
    def get_queue_status(self) -> QueueStatus: ...
```
`execute()` is the **only** sanctioned path to the outside world. Every LLM adapter
(`llm_cloud.py`, `llm_ollama.py`) and the Gmail reporter (`gmail_reporter.py`) call **through**
`execute()`; direct network calls are forbidden and asserted against in tests.

### 2.2 `execute()` pipeline
```
execute(api_call, service, *a, **kw)
 1. resolve service limits from config (default | llm | gmail)
 2. RateLimiter.allow(service)?
       ├─ yes → admit
       └─ no  → FIFO.enqueue(request)            # backpressure if full (§3)
 3. acquire concurrency slot (≤ concurrent_max)
 4. RetryPolicy.run(api_call, *a, **kw)          # backoff on transient failures
 5. on success: TOKEN-INTERCEPTION HOOK (§4) → TokenTracker
 6. StructuredLogger.log(call meta, latency, outcome, tokens)
 7. release slot; drain queue if windows reset
 8. return result  (or controlled BackpressureStatus / GatekeeperError)
```

### 2.3 Service routing
`service ∈ {"default","llm","gmail"}` selects the limit profile from `config/rate_limits.json`
(`PLAN.md §5.3`). Unknown service → `default` (logged).

---

## 3. FIFO Queue — Thread-Safe Implementation & Backpressure

### 3.1 Thread-safe FIFO
- **Synchronous path:** `queue.Queue(maxsize=queue_max_depth)` — intrinsically thread-safe
  (mutex + condition vars); producers `put_nowait`, the drain worker `get`s.
- **Async path:** `asyncio.Queue(maxsize=queue_max_depth)` for FastMCP async tool handlers; a single
  drain coroutine awaits capacity and rate-window resets.
- Concurrency cap enforced via a `threading.Semaphore(concurrent_max)` (or `asyncio.Semaphore`).
- No shared mutable state outside the queue + counters, all guarded by the queue's locks / a
  dedicated `Lock` (avoids deadlock; uses context managers per Guidelines §15.2).

### 3.2 Drain mechanism
A drain worker releases queued requests in **arrival order** as soon as a rate window frees a slot,
preserving fairness (FIFO) and honoring `concurrent_max`.

### 3.3 Backpressure signaling
When `FIFO.qsize() == queue_max_depth` and a new request arrives:
- `execute()` returns a **`BackpressureStatus(retry_after=…, queue_depth=…)`** (it does **not** raise,
  does **not** drop, does **not** crash — satisfies "never crashes on overflow").
- The orchestrator interprets backpressure by **slowing the turn cycle** (sleep `retry_after`, then
  retry the same logical step) — i.e. throttling arrival rate `λ` at the source.
- `get_queue_status()` exposes `{depth, capacity, in_flight, dropped:0, backpressure_events}` for
  monitoring and for the GUI/telemetry.

---

## 4. Token-Interception Hook (telemetry integration)

### 4.1 Responsibility
On every **successful LLM** call, `execute()` reads usage from the provider response and **delegates
persistence** to the `TokenTracker` (owned by `PRD_token_budget.md`). The gatekeeper does **not**
itself compute cost or write the telemetry file — it is the *interception point* only (single
responsibility, DRY).

### 4.2 Extraction contract
```python
usage = extract_usage(response)   # provider-agnostic adapter
#   -> {"prompt_tokens": int, "completion_tokens": int}
token_tracker.record(service="llm",
                     prompt_tokens=usage["prompt_tokens"],
                     completion_tokens=usage["completion_tokens"],
                     model=model_id)
```
- Cloud providers expose `usage.prompt_tokens` / `usage.completion_tokens`; Ollama exposes
  `prompt_eval_count` / `eval_count` — both normalised by `extract_usage()`.
- If usage is **absent** (some local models), fall back to an estimator (`len(prompt)/4`) flagged
  `estimated=True` so cost figures stay conservative.
- Gmail and non-LLM calls record **zero tokens** but still log latency/outcome.

### 4.3 Failure isolation
Telemetry recording is best-effort: a TokenTracker error is caught, logged, and **never** fails the
underlying API call (telemetry must not break gameplay).

---

## 5. Functional Requirements, I/O Contracts & Metrics

### 5.1 Functional requirements
| ID | Requirement |
|----|-------------|
| GK-F1 | `execute()` is the sole external-call path (LLM + Gmail); no bypass. |
| GK-F2 | Per-service rate limits from `config/rate_limits.json` (versioned, no hardcoding). |
| GK-F3 | FIFO queue, thread-safe (`queue.Queue` / `asyncio.Queue`), `maxsize=queue_max_depth`. |
| GK-F4 | Concurrency cap `concurrent_max` via semaphore. |
| GK-F5 | Retry transient failures with backoff (`max_retries`, `retry_after_seconds`). |
| GK-F6 | Backpressure status on full queue — never crash, never drop. |
| GK-F7 | Token-interception hook → TokenTracker on successful LLM calls. |
| GK-F8 | Structured logging of every call (service, latency, outcome, tokens). |
| GK-F9 | `get_queue_status()` returns live depth/stats. |

### 5.2 I/O contracts
**`execute` Input:** `(api_call: Callable, *args, service: str, **kwargs)`
**`execute` Output:** `api_call`'s result · **or** `BackpressureStatus` · **or** controlled
`GatekeeperError` after exhausted retries (never an uncaught exception to the caller).
**`get_queue_status` Output:** `QueueStatus{depth, capacity, in_flight, backpressure_events, dropped=0}`.

### 5.3 Performance metrics
| Metric | Target |
|--------|--------|
| Dropped requests | **0** (by design) |
| Crash on overflow | **0** |
| FIFO ordering correctness | 100 % |
| Retry success on injected transient faults | ≥ 95 % within `max_retries` |
| Overhead per admitted call | ≤ 2 ms (excluding network) |
| Token capture rate on LLM calls | 100 % (recorded or estimated) |

---

## 6. Hard Constraints, Edge Cases, Alternatives, Rationale

### 6.1 Hard constraints
- Zero external calls bypass the gatekeeper (architecture test enforced).
- Limits config-sourced; **never** hardcoded (Guidelines §7.2, Table 1).
- Files ≤150 LOC (limiter / retry / queue / gatekeeper split across modules).
- Never crash on overflow; never drop a request.

### 6.2 Edge cases
| Case | Behaviour |
|------|-----------|
| Queue full | Return `BackpressureStatus`; orchestrator slows turn cycle. |
| All retries exhausted | Return controlled `GatekeeperError` (logged), caller degrades gracefully. |
| Permanent 4xx (auth/validation) | No retry; surface immediately. |
| Provider omits token usage | Estimate (`len/4`), flag `estimated=True`. |
| TokenTracker write error | Caught + logged; API result still returned. |
| Concurrent burst > concurrent_max | Excess queued FIFO; semaphore gates. |
| `queue_max_depth=0` config | Degenerate: immediate backpressure (validated/allowed). |
| Clock skew on window reset | Monotonic clock used for windows. |

### 6.3 Alternatives considered
| Alternative | Verdict | Rationale |
|-------------|---------|-----------|
| Per-call decorators (no central gate) | **Rejected** | Violates §5.1; duplicated retry/limit logic (anti-DRY). |
| Drop-on-overflow (lossy) | **Rejected** | Brief: "queue, do not drop"; lose turns/telemetry. |
| Unbounded queue | Rejected | Memory blow-up; no backpressure signal. |
| Token-tracking inside gatekeeper | Rejected | Violates single responsibility; delegated to TokenTracker. |
| Raise on full queue | Rejected | "Never crash on overflow" → status object instead. |

### 6.4 Technical rationale
A single chokepoint gives us **one** place to enforce limits, retries, backpressure, logging, and
token capture — eliminating duplication and guaranteeing the "never crash / never drop" invariant.
Delegating persistence to the TokenTracker keeps the gatekeeper single-responsibility and testable.

---

## 7. Acceptance Criteria
- [ ] Architecture test proves no module performs network IO outside `execute()`.
- [ ] FIFO preserves arrival order under concurrency.
- [ ] Overflow yields `BackpressureStatus`, zero crashes, zero drops.
- [ ] Transient faults retried with backoff; permanent faults not retried.
- [ ] Every successful LLM call records tokens to the TokenTracker.
- [ ] Limits read only from config; hardcode scan clean.
- [ ] Coverage ≥85 % for `infra/gatekeeper|rate_limiter|retry|queue_monitor`; `ruff` clean.

## 8. Step-by-Step Test Scenarios
1. **Chokepoint:** patch socket layer; assert all LLM/Gmail calls traverse `execute()` (spy counter).
2. **Rate gate:** set `rpm=2`; fire 5 calls ⇒ 2 execute, 3 enqueued then drained on window reset; order preserved.
3. **Concurrency:** `concurrent_max=1`; 3 parallel calls ⇒ serialised; semaphore never exceeded.
4. **Backpressure:** `queue_max_depth=2`, saturate ⇒ next call returns `BackpressureStatus`; process does not crash; `get_queue_status().dropped == 0`.
5. **Retry:** mock 2 transient 503s then 200 ⇒ succeeds on 3rd attempt; backoff delays observed.
6. **Permanent:** mock 401 ⇒ no retry; controlled error returned.
7. **Token hook:** mock LLM response `usage={prompt:850, completion:90}` ⇒ TokenTracker.record called with those values.
8. **Token estimate:** response without usage ⇒ recorded with `estimated=True`.
9. **Telemetry isolation:** force TokenTracker to raise ⇒ API result still returned; error logged.

*End of `PRD_gatekeeper.md`.*
