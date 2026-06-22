# PRD (Per-Mechanism) — Token Economics, Real-Time Telemetry & Budget Tracker
## `marl-cop-thief` · Mechanism: Master Token Accounting Specification

| Field | Value |
|-------|-------|
| Mechanism ID | `MECH-TOKEN-BUDGET` |
| Document version | 1.00 |
| Parent docs | [`PRD.md`](./PRD.md) · [`PLAN.md`](./PLAN.md) · [`TODO.md`](./TODO.md) (NEW mechanism — Step 4 expansion) |
| Source modules | `infra/token_tracker.py`, `infra/cost_model.py`, `config/setup.json → token_budget`, `data/token_usage.json` |
| Upstream hook | [`PRD_gatekeeper.md §4`](./PRD_gatekeeper.md) (token-interception) |
| Injected into | [`PRD_gmail_oauth.md §4`](./PRD_gmail_oauth.md) (`telemetry` block) |
| Standard | Dr. Segal *Guidelines v3.00* (§11 costs & budget, §2.3, §9 research) |
| Status | Draft — approve before implementing (per Dr. Segal oral instruction) |

> **Mandate.** The project must perform **strict, real-time token telemetry and cost accounting**.
> The Gatekeeper live-streams usage to `data/token_usage.json`; the SDK injects a `telemetry` block
> into both report schemas; spend is held under a hard ceiling.

---

## 1. Theoretical & Mathematical Background

### 1.1 Token accounting model
Every LLM call consumes `p` **prompt (input) tokens** and produces `c` **completion (output) tokens**.
Lifecycle totals are simple accumulators:
```
P_total = Σ_i p_i          (input tokens accumulated)
C_total = Σ_i c_i          (output tokens accumulated)
```
Cost is a linear function of the two accumulators against per-million rates:
```
cost_usd = (P_total / 1e6) · rate_in  +  (C_total / 1e6) · rate_out
```

### 1.2 Per-turn unit & per-game estimate
A **joint turn** (one Cop decision + one Thief decision, including encode + parse LLM calls) costs on
average:
```
p_turn ≈ 850 input tokens     c_turn ≈ 90 output tokens
```
A **full game** = `num_games (6)` sub-games × up to `max_moves (25)` moves = **150 joint turns**:
```
P_game = 150 · 850 = 127,500 input tokens
C_game = 150 ·  90 =  13,500 output tokens
```
(`150 = 6 × 25` is the worst-case upper bound; captures end sub-games earlier, so this is conservative.)

### 1.3 Established lifecycle budget (baseline)
Summing the full development lifecycle — the **4 sanity-progression stages** (2×2 → 3×3 → 4×4 → 5×5),
the **automated TDD suites** (many mocked + some live runs), and **3 bonus series** — the established
lifecycle budget is fixed at:
```
LIFECYCLE_INPUT_BUDGET  = 1,500,000 input tokens
LIFECYCLE_OUTPUT_BUDGET =   180,000 output tokens
```
(≈ 11.8 full-game equivalents of input headroom over the raw per-game figure, covering retries,
sensitivity sweeps, and mocked-but-occasionally-live tests.)

### 1.4 Cost calculation (baseline)
Using standard lightweight-LLM rates:
```
rate_in  = $0.15 per 1,000,000 input tokens
rate_out = $0.60 per 1,000,000 output tokens

cost = (1,500,000 / 1e6)·0.15 + (180,000 / 1e6)·0.60
     =  0.225            +  0.108
     =  $0.333  ≈  $0.33 USD   (estimated project lifecycle cost)
```
**Hard budget ceiling = $5.00 USD** — a ~15× safety margin over the $0.33 estimate. Crossing the
ceiling halts further *billable* LLM calls (see §4.3).

### 1.5 Reconciling per-game vs lifecycle
| Quantity | Input | Output | Cost |
|----------|-------|--------|------|
| Per joint turn | 850 | 90 | — |
| Per full game (150 turns) | 127,500 | 13,500 | ≈ $0.027 |
| **Lifecycle budget** | **1,500,000** | **180,000** | **$0.33** |
| **Hard ceiling** | — | — | **$5.00** |

---

## 2. Architecture & Data Flow
```
LLM call (any adapter)
   └─▶ ApiGatekeeper.execute()                       [PRD_gatekeeper.md §4]
        └─ extract_usage(response) → {prompt_tokens, completion_tokens}
             └─▶ TokenTracker.record(service, p, c, model, estimated?)
                  ├─ update in-memory accumulators (thread-safe)
                  ├─ CostModel.cost(P_total, C_total) → estimated_cost_usd
                  ├─ evaluate status (OK | WARN | CEILING_HIT)
                  └─ live-stream snapshot → data/token_usage.json   (atomic write)
SDK.build_*_report()
   └─ TokenTracker.snapshot() → inject `telemetry` block into internal_game.json / bonus_report.json
```
- **TokenTracker** (`infra/token_tracker.py`): the single owner of accumulators + persistence.
- **CostModel** (`infra/cost_model.py`): pure function `cost(P, C)` using config rates (no hardcoding).
- The Gatekeeper only *intercepts and delegates* (single responsibility); the Tracker *owns the math*.

---

## 3. Real-Time Telemetry Contracts

### 3.1 Live stream file — `data/token_usage.json`
Written (atomically: temp-file + `os.replace`) after every recorded call.
```json
{
  "version": "1.00",
  "updated_at": "2026-06-22T10:15:03+03:00",
  "input_accumulated": 412345,
  "output_accumulated": 50231,
  "estimated_cost_usd": 0.0920,
  "status": "OK",
  "ceiling_usd": 5.00,
  "by_service": {
    "llm":   { "input": 412345, "output": 50231, "calls": 486, "estimated_share": 0.0 },
    "gmail": { "input": 0,      "output": 0,     "calls": 7 }
  },
  "by_model": {
    "llm-light": { "input": 412345, "output": 50231 }
  }
}
```

### 3.2 Injected `telemetry` block (reports)
The SDK injects the following into **both** `internal_game.json` and `bonus_report.json` (per
`PRD_gmail_oauth.md §4.1`):
```json
"telemetry": {
  "input_accumulated":  127500,
  "output_accumulated": 13500,
  "estimated_cost_usd": 0.0270,
  "status": "OK"
}
```
- **`status` enum:** `OK` (cost < warn threshold) · `WARN` (≥ `warn_ratio`·ceiling, default 0.8) ·
  `CEILING_HIT` (≥ ceiling).
- Per `PRD_gmail_oauth.md §4.3`, the `telemetry` block is **excluded from the K3 `agreement_view`
  hash** (each group measures its own tokens) — it is reported but does not affect mutual agreement.

### 3.3 Config (`config/setup.json → token_budget`, versioned)
```json
"token_budget": {
  "version": "1.00",
  "rates": { "input_per_million_usd": 0.15, "output_per_million_usd": 0.60 },
  "lifecycle_budget": { "input_tokens": 1500000, "output_tokens": 180000 },
  "ceiling_usd": 5.00,
  "warn_ratio": 0.80,
  "per_turn_estimate": { "input": 850, "output": 90 },
  "enforce_ceiling": true,
  "usage_file": "data/token_usage.json"
}
```

---

## 4. Functional Requirements, I/O Contracts & Metrics

### 4.1 Functional requirements
| ID | Requirement |
|----|-------------|
| TB-F1 | `TokenTracker.record(service, prompt_tokens, completion_tokens, model, estimated)` updates accumulators thread-safely. |
| TB-F2 | `CostModel.cost(P, C)` computes USD from **config** rates (no hardcoding). |
| TB-F3 | After each record, live-stream an atomic snapshot to `data/token_usage.json`. |
| TB-F4 | Compute `status` (OK/WARN/CEILING_HIT) from cost vs `warn_ratio`·ceiling and ceiling. |
| TB-F5 | SDK injects the `telemetry` block into both report schemas. |
| TB-F6 | Telemetry excluded from K3 agreement hash. |
| TB-F7 | On `enforce_ceiling=true` and `CEILING_HIT`, block further **billable** LLM calls (graceful, not crash). |
| TB-F8 | Estimated-usage calls flagged; `estimated_share` surfaced. |
| TB-F9 | `snapshot()` returns the current telemetry dict for reports/GUI. |

### 4.2 I/O contracts
**`record` In:** `(service:str, prompt_tokens:int≥0, completion_tokens:int≥0, model:str, estimated:bool=False)` · **Out:** updated `TelemetrySnapshot`.
**`CostModel.cost` In:** `(P:int, C:int)` · **Out:** `float USD` (rounded 6 dp).
**`snapshot` Out:** `{input_accumulated, output_accumulated, estimated_cost_usd, status, by_service, by_model}`.

### 4.3 Ceiling enforcement behaviour
- At `CEILING_HIT` with `enforce_ceiling=true`: the Gatekeeper, consulting `TokenTracker.status()`,
  **refuses new billable LLM calls** and returns a controlled `BudgetExceeded` status (never crashes);
  mocked/test calls (zero-cost) and Gmail sends still proceed.
- The orchestrator surfaces the halt, persists state, and the run can resume after the ceiling/config
  is raised. (At the $0.33 baseline vs $5.00 ceiling this should never trigger in practice — it is a
  guardrail.)

### 4.4 Performance metrics
| Metric | Target |
|--------|--------|
| Token capture coverage of LLM calls | 100 % (recorded or estimated) |
| Telemetry write overhead per call | ≤ 2 ms (atomic small-file write) |
| Cost-figure accuracy vs manual recompute | exact (deterministic linear model) |
| K3 false-mismatch caused by telemetry | **0** |
| Lifecycle spend | ≈ $0.33; **never** > $5.00 |
| Concurrency safety (lost updates) | 0 lost records under parallel calls |

---

## 5. Hard Constraints, Edge Cases, Alternatives, Rationale

### 5.1 Hard constraints
- Rates, budgets, ceiling **config-sourced & versioned** (no hardcoding; Guidelines §7.2).
- Telemetry must **never** break gameplay (best-effort persistence; isolation per `PRD_gatekeeper.md §4.3`).
- Telemetry **excluded** from the agreement hash.
- Files ≤150 LOC (tracker / cost model / writer split if needed); thread-safe.

### 5.2 Edge cases
| Case | Behaviour |
|------|-----------|
| Provider omits usage | Estimate `prompt≈len/4`; `estimated=True`; raise `estimated_share`. |
| `data/token_usage.json` unwritable | Log warning; keep in-memory accumulators; continue. |
| Concurrent records | Guard accumulators with a lock; no lost updates. |
| Negative/garbage token counts | Reject (treat as 0) + log; never corrupt totals. |
| Cost crosses warn ratio | `status=WARN`; surfaced in telemetry + GUI. |
| Cost crosses ceiling | `status=CEILING_HIT`; block billable LLM calls if `enforce_ceiling`. |
| Mixed models | Track `by_model`; cost uses per-model rate if provided, else default. |
| Resume after halt | Reload accumulators from `data/token_usage.json` on startup. |

### 5.3 Alternatives considered
| Alternative | Verdict | Rationale |
|-------------|---------|-----------|
| Post-hoc cost from provider dashboard | **Rejected** | Not real-time; no in-run guardrail; brief wants live telemetry. |
| Track tokens inside the Gatekeeper | **Rejected** | Violates single-responsibility; delegated to TokenTracker (DRY). |
| Include telemetry in K3 hash | **Rejected** | Per-group token differences → spurious disagreement (0/0 bonus). |
| Hard-stop crash on ceiling | **Rejected** | Must degrade gracefully; return `BudgetExceeded` status instead. |
| Estimate-only (ignore provider usage) | Rejected | Less accurate; use real usage, estimate only as fallback. |

### 5.4 Technical rationale
A single Tracker + pure CostModel gives one authoritative, testable source of spend; live atomic
writes provide real-time observability and crash-resumable accumulators; excluding self-measured
telemetry from the agreement hash protects K3; and the $5.00 ceiling (15× the $0.33 estimate) is a
cheap safety net that never crashes the run.

---

## 6. Acceptance Criteria
- [ ] Per-game math reproduces 127,500 input / 13,500 output for 150 turns at 850/90.
- [ ] Lifecycle cost recompute equals **$0.33** for 1.5M/180k at $0.15/$0.60.
- [ ] `record()` updates accumulators thread-safely with zero lost updates.
- [ ] `data/token_usage.json` updated atomically after each call.
- [ ] `telemetry` block injected into both report schemas; **excluded** from K3 hash.
- [ ] `CEILING_HIT` blocks billable LLM calls gracefully (no crash).
- [ ] Rates/budgets/ceiling entirely config-sourced; hardcode scan clean.
- [ ] Coverage ≥85 % for `infra/token_tracker|cost_model`; `ruff` clean.

## 7. Step-by-Step Test Scenarios
1. **Per-turn → per-game:** record 150 turns of `(850, 90)` ⇒ `input_accumulated=127500`, `output_accumulated=13500`.
2. **Lifecycle cost:** set `P=1_500_000, C=180_000` ⇒ `CostModel.cost == 0.333000` (≈ $0.33).
3. **Status thresholds:** with ceiling $5, warn 0.8 ⇒ cost $4.0 → `WARN`; $5.0 → `CEILING_HIT`.
4. **Ceiling enforcement:** `enforce_ceiling=true`, force `CEILING_HIT` ⇒ next billable LLM call returns `BudgetExceeded`; process alive; Gmail send still allowed.
5. **Estimate fallback:** response without usage ⇒ recorded `estimated=True`; `estimated_share > 0`.
6. **Atomic write:** kill mid-write (simulated) ⇒ `data/token_usage.json` never partially corrupt (temp+replace).
7. **Concurrency:** 1 000 parallel `record()` calls ⇒ totals exact (no lost updates).
8. **Report injection:** build internal + bonus reports ⇒ both contain a `telemetry` block with the four fields.
9. **K3 isolation:** two records with identical facts, different telemetry ⇒ identical `agreement_view` hash (telemetry excluded).
10. **Resume:** restart with existing `data/token_usage.json` ⇒ accumulators reloaded.

*End of `PRD_token_budget.md`.*
