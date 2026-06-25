# TODO — Master Work Breakdown Structure
## Dual AI Agent Conversation via MCP Servers — Dec-POMDP Cop & Thief Chase

| Field | Value |
|-------|-------|
| Document version | 1.00 |
| Depends on | [`PRD.md`](./PRD.md), [`PLAN.md`](./PLAN.md) (both approved) |
| Convention | Each task is atomic. Per code module we generate: skeleton & typing → core logic → validation/gatekeeper hooks → positive unit test → edge/failure fixture → Ruff-compliant docstrings. |
| Definition of Done (per task) | Code ≤150 LOC, `ruff check` clean, tests green, coverage not reduced below 85 %, no hardcoded values, runs via `uv`. |
| Status legend | `[ ]` not started · `[~]` in progress · `[x]` done |

> **Tasks are globally numbered #1 … #N and grouped into 10 sequential engineering phases.**

---

## ★ Homestretch Completion Log (validated milestones)

These cross-cutting milestones are **done and verified** (full suite green, `ruff` clean):

- [x] **Dec-POMDP RL stabilization** — three-tier strategy stable: Tier-1 tabular Q-Learning
  (Bellman TD update + ε-greedy decay) with the **Tier-2 Conway-geometry override** rescuing the
  cold/uninformed Q-table, validated by a silent **400-episode warmup spark**. Proven offline by
  `diagnostic_runner.py` (capture by turn 5; first geometry override on turn 1). Files:
  `domain/strategy/qtable.py`, `orchestrator/controller.py`.
- [x] **Zero-dependency `.env` autoloader** — `config/env_loader.py` (`load_env_once`) wired into
  `ConfigManager.__init__`; idempotent, non-overriding (shell exports still win). **No `python-dotenv`
  dependency.** Removes any need for manual shell `export`/`source` of secrets.
- [x] **Headless Google OAuth2 loopback resolved** — desktop flow mints and vaults `token.json`
  locally (scope `gmail.modify`, zero passwords). One-time browser consent already completed.
- [x] **Gatekeeper generic passthrough** — `ApiGatekeeper.execute(func, *args, service, **kwargs)`
  added as the FIFO-gated chokepoint for non-LLM dispatches (e.g. Gmail), per `PRD_gatekeeper.md §2.1`.
- [x] **Milestone 3 — Broadcast "Television" & JSONL audit logger** — one-way SSE server
  (`ui/server.py`, Starlette) + single-file vanilla `ui/static/index.html` (5×5 matrix, comms
  intercept, turn/epistemic/cost top-bar; zero CDN), and append-only `reporting/logger.py`
  (`data/game_audit.jsonl`, `jq`-parseable). UI is strictly receive-and-render (no game logic).

### Milestone 4 — Cloudflare Tunneling & Inter-Group Verification (OPEN)
- [x] **M4.0** Network matrix in config — `config/setup.json → network` (two URLs/team: cop + thief)
  parsed by `ConfigManager.network` (`config/aux_models.py::NetworkConfig`); config-split keeps every
  config module < 120 lines.
- [x] **M4.0** `cloudflared` secured as a userland binary in `bin/` (git-ignored; non-root install).
- [x] **M4.1** Spin two Cloudflare tunnels → local Cop (`:8001`) / Thief (`:8002`); write public HTTPS
  URLs into the `network` block; assert revocable-token security. *(`switchboard.py` + `app.py` boot tunnels with the servers; tokens fail-closed.)*
- [x] **M4.2** Wire `network` endpoints into the FastMCP client/orchestrator for cross-host play. *(`RemoteMoveClient` — MCP `Client` over `/mcp`; control panel + `challenge` drive cross-host, partner URL is runtime input.)*
- [x] **M4.3** Inter-group bonus handshake: full 6-sub-game bilateral series, **mutual SHA-256
  agreement** sealed and emailed. *(`ChallengeRunner` + `reconcile_agreement`; mismatch ⇒ 0/0. Live partner run = remaining cycle #3.)*

### Architecture / Tooling notes
- **`src/cop_thief/diagnostic_runner.py`** — permanent **offline, zero-cost** Dec-POMDP reactor probe.
  Runs the real `GameLoopController` with **mocked** LLM encoder/parser (no DeepSeek/Anthropic calls),
  seeded for reproducibility, under a self-imposed turn guillotine. Use it to regression-test pursuit
  math without spending tokens: `uv run python -m cop_thief.diagnostic_runner`.
- **Gmail OAuth ignition is permanently bypassed** for routine runs via the vaulted `token.json`
  (auto-refreshed); the live browser handshake is **not** re-triggered unless the token is revoked.
- **Secrets workflow:** populate `.env` (copied from `.env-example`); the autoloader injects them at
  startup. Manual `export FOO=…` / `source .env` steps are **obsolete** and intentionally omitted.

---

## ★★ AS-BUILT RECONCILIATION (v2.0 — authoritative status)

The project is **functionally complete and submission-ready**: every **PRD §4.1 functional requirement**
is implemented, with **109 tests green / ~95 % coverage / `ruff` clean / all files ≤150 LOC**. This
section is the **source of truth** for status; the granular WBS (#1–#430) below is the original
fine-grained plan, kept as a historical record and **superseded where the build consolidated or diverged**.

**Built & verified (as-built modules):**
- Domain & rules → `domain/` (`state.py`, `grid.py`, `geometry.py`, `constants.py`, `move_language.py`):
  the planned `RulesEngine`+Mixin decomposition (#19–#63) was **consolidated** here (same behaviour, fewer files).
- Strategy → `domain/strategy/` minimax + Conway Angel–Devil + self-play RL + opponent model
  (`minimax.py`, `evaluation.py`, `features.py`, `opponent.py`, `selfplay.py`); tabular Q (`qtable.py`)
  kept as the documented baseline. See [`STRATEGY.md`](./STRATEGY.md).
- Config / Gatekeeper / SDK / MCP servers / NL / Reporting / GUI / Logger → built & tested (Phases 2–8).
- Decentralized match play, control panel, tunnels, cross-host challenge, mutual-agreement reconcile →
  Milestone 5 (#431–#449).

**Genuinely remaining (the planned next cycles):**
1. **README polish + screenshots** (UI panel + terminal) — covers #307, #345–#347, #351, #379–#380, #430.
2. **Active injection counter-measure** (escalating response to a cheating opponent) — new SEC item.
3. **Real inter-group game run** vs a live opponent — #344, #349, #376, #386, #444.
4. **Dispute log archive** (immutable per-game evidence bundle to prove opponent cheating) — extends #282/#440.
5. ~~§9.2 `bonus_game` schema convergence~~ — **done** (`reporting/bonus_report.py`, #453); fed real metadata at game time.

**Superseded / not used (out of scope — do not implement):**
- Cloud target **Prefect Cloud** (#353–#360) → we use **Cloudflare tunnels** (`switchboard.py`).
- **ngrok / Nginx / Ollama** tunnel & local-LLM alternatives (#361–#366) → cloud LLM API only.
- `RulesEngine` + `Movement/Capture/Turn/BarrierMixin` (#32–#63) and separate `BaseAgent`/`CopAgent`/
  `ThiefAgent` classes (#261–#267) → **consolidated** into `domain/` + SDK + strategy.
- Staged sanity runs 2×2→4×4 (#328–#342) → supported by config (`grid_size`) but not run as separate
  suites; the 5×5 game is validated end-to-end.

---

## PHASE 1 — Core Domain, Grid Mechanics & State Machine (Dec-POMDP)

### 1.A constants.py
- [x] **#1** Create `src/cop_thief/constants.py` skeleton with module docstring & typing imports.
- [x] **#2** Define `Direction` Enum (8 directions + STAY) with `(dr, dc)` vectors.
- [x] **#3** Define `AgentRole` Enum (`COP`, `THIEF`) and `ActionType` Enum (`MOVE`, `PLACE_BARRIER`).
- [x] **#4** Define `SubGameOutcome` Enum (`COP_WINS`, `THIEF_WINS`, `VOID_TECHNICAL`).
- [x] **#5** Add immutable physical/math constants (default vision band labels, tie-break order).
- [x] **#6** Write positive unit test `tests/unit/test_constants.py` asserting enum members & vectors.
- [ ] **#7** Add edge-case fixture: assert no duplicate direction vectors, STAY = (0,0).
- [ ] **#8** Inject Ruff-compliant docstrings explaining *why* each enum exists.

### 1.B Cell & Grid
- [x] **#9** Create `domain/grid.py` skeleton; define `Cell` dataclass (row, col) with typing.
- [x] **#10** Implement `Cell` equality, hashing, and neighbor computation.
- [x] **#11** Define `Grid` class skeleton (rows, cols sourced from config, not literals).
- [x] **#12** Implement `Grid.in_bounds(cell)` core logic.
- [x] **#13** Implement `Grid.neighbors(cell, include_diagonal=True)` core logic.
- [x] **#14** Add validation hook: reject non-positive grid dimensions (raise `ValueError`).
- [x] **#15** Write positive test `test_grid.py`: bounds & neighbors on a 5×5.
- [x] **#16** Write edge-case fixture: 1×1, 2×2, and non-square (3×2) grids.
- [x] **#17** Write edge-case fixture: corner/edge cells have correct reduced neighbor sets.
- [x] **#18** Inject docstrings (Input/Output/Setup per building-block format).

### 1.C BoardStateMachine
- [ ] **#19** Create `domain/board_state.py` skeleton; define `BoardState` dataclass (cop, thief, barriers:set, barriers_left, move_count).
- [ ] **#20** Add typing & immutability strategy (copy-on-write transitions).
- [ ] **#21** Implement `BoardStateMachine.initial_state()` with random start positions (seedable).
- [ ] **#22** Implement strategic start option (config flag random vs strategic).
- [ ] **#23** Implement `apply(state, action) -> BoardState` core transition (the `P` function).
- [ ] **#24** Implement barrier-cell impassability in transition (both agents blocked).
- [ ] **#25** Add validation hook: reject transitions producing out-of-bounds / barrier-occupied cells.
- [ ] **#26** Add validation hook: ensure cop & thief never spawn on the same cell or on a barrier.
- [ ] **#27** Write positive test `test_board_state.py`: deterministic transition with fixed seed.
- [ ] **#28** Write edge-case fixture: move into wall is clamped/rejected per policy.
- [ ] **#29** Write edge-case fixture: move into barrier rejected; STAY allowed.
- [ ] **#30** Write edge-case fixture: random start reproducible under a fixed seed.
- [ ] **#31** Inject docstrings explaining the Dec-POMDP `S`/`P` mapping.

### 1.D Rules — MovementMixin
- [ ] **#32** Create `domain/rules/movement_mixin.py` skeleton (single concern).
- [ ] **#33** Implement 8-direction movement resolution with edge clamping.
- [ ] **#34** Add validation hook: legal-move set generator for a given cell.
- [ ] **#35** Write positive test `test_movement_mixin.py`.
- [ ] **#36** Write edge-case fixture: diagonal at corner, blocked diagonal past a barrier.
- [ ] **#37** Inject docstrings; confirm mixin overrides nothing.

### 1.E Rules — BarrierMixin
- [ ] **#38** Create `domain/rules/barrier_mixin.py` skeleton.
- [ ] **#39** Implement barrier placement on the cop's current cell.
- [ ] **#40** Implement quota enforcement (`max_barriers` from config; thief = 0).
- [ ] **#41** Add validation hook: reject placement when quota exhausted or thief attempts it.
- [ ] **#42** Write positive test `test_barrier_mixin.py`.
- [ ] **#43** Write edge-case fixture: 6th barrier rejected; thief barrier rejected; barrier on occupied cell rule.
- [ ] **#44** Inject docstrings.

### 1.F Rules — CaptureMixin
- [ ] **#45** Create `domain/rules/capture_mixin.py` skeleton.
- [ ] **#46** Implement same-cell capture detection.
- [ ] **#47** Add validation hook: capture only valid on cop's arrival turn.
- [ ] **#48** Write positive test `test_capture_mixin.py`.
- [ ] **#49** Write edge-case fixture: adjacent-but-not-same → no capture; simultaneous swap rule.
- [ ] **#50** Inject docstrings.

### 1.G Rules — TurnMixin
- [ ] **#51** Create `domain/rules/turn_mixin.py` skeleton.
- [ ] **#52** Implement turn arbiter (thief-first default, alternation, one action/turn).
- [ ] **#53** Add validation hook: enforce `move_count ≤ max_moves`.
- [ ] **#54** Write positive test `test_turn_mixin.py`.
- [ ] **#55** Write edge-case fixture: terminal at `max_moves` triggers thief win.
- [ ] **#56** Inject docstrings.

### 1.H RulesEngine (composition)
- [ ] **#57** Create `domain/rules/rules_engine.py` composing the four mixins.
- [ ] **#58** Implement `validate(action, state)` unified gate.
- [ ] **#59** Implement `terminal_check(state) -> SubGameOutcome | None`.
- [ ] **#60** Add validation hook: reject malformed `Action` objects.
- [ ] **#61** Write positive test `test_rules_engine.py` (full legal turn).
- [ ] **#62** Write edge-case fixture: illegal action returns graceful rejection, not exception leak.
- [ ] **#63** Inject docstrings; confirm ≤150 LOC (split if needed).

### 1.I ScoringEngine
- [ ] **#64** Create `domain/scoring.py` skeleton + `ScoringMixin`.
- [ ] **#65** Implement scoring from `setup.json` (cop_win=20, thief_win=10, cop_loss=5, thief_loss=5).
- [ ] **#66** Implement per-sub-game and accumulated totals (max 90 / min 30 invariants).
- [ ] **#67** Add validation hook: assert scoring values are config-sourced & immutable at runtime.
- [ ] **#68** Write positive test `test_scoring.py` over both outcomes.
- [ ] **#69** Write edge-case fixture: void sub-game scores nothing; totals invariant check.
- [ ] **#70** Inject docstrings citing the immutable scoring table.

### 1.J Domain integration & docs
- [ ] **#71** Wire `domain/__init__.py` public exports (relative imports only).
- [ ] **#72** Integration test `tests/integration/test_sub_game_engine.py`: a scripted full sub-game.
- [ ] **#73** Author [`PRD_nl_protocol.md`](./PRD_nl_protocol.md) stub (filled in Phase 7).
- [ ] **#74** Author [`PRD_rl_qtable.md`](./PRD_rl_qtable.md) stub (filled in Phase 7).
- [ ] **#75** Phase-1 review: confirm every file ≤150 LOC and zero hardcoded params.

---

## PHASE 2 — Enterprise Infrastructure (Config Managers, Versioning, uv, Ruff)

### 2.A Project bootstrap (uv)
- [x] **#76** `uv init` the project; create `pyproject.toml` (name, version `1.00`, description, license).
- [ ] **#77** Configure `[project]` Python `>=3.10` and package layout (`src/cop_thief`).
- [ ] **#78** Add runtime deps via `uv add` (fastmcp, google-api-python-client, requests/httpx).
- [ ] **#79** Add dev deps via `uv add --dev` (pytest, pytest-cov, ruff).
- [ ] **#80** Generate & commit `uv.lock`; verify `uv sync` reproduces the env.
- [ ] **#81** Create `src/cop_thief/__init__.py` exporting `__version__ = "1.00"` and `__all__`.
- [ ] **#82** Audit task: grep the repo to prove **zero** `pip`/`virtualenv`/`python -m` usages.
- [ ] **#83** Add `uv run` wrappers/notes to README for every dev command.

### 2.B Ruff configuration
- [x] **#84** Add `[tool.ruff]` (`line-length=100`, `target-version="py310"`).
- [x] **#85** Add `[tool.ruff.lint]` select `E,F,W,I,N,UP,B,C4,SIM`; ignore `E501` if needed.
- [ ] **#86** Run `uv run ruff check` and drive violations to **0**.
- [ ] **#87** Document the lint gate in README contribution guidelines.

### 2.C Coverage configuration
- [x] **#88** Add `[tool.coverage.run]` `source=["src"]`, omit `main.py`, `tests/*`, `**/gui/*`.
- [x] **#89** Add `[tool.coverage.report] fail_under = 85`.
- [ ] **#90** Wire `uv run pytest --cov` and confirm the gate fails under 85 %.

### 2.D ConfigManager
- [x] **#91** Create `config/models.py` skeleton: `BaseConfigModel` + typed `GameConfig`, `ScoringConfig`.
- [x] **#92** Add typing & defaults matching PRD §3.4 / config Table 3.
- [x] **#93** Create `config/config_manager.py` skeleton (load JSON/YAML, single source of truth).
- [x] **#94** Implement `ConfigManager.get(key, default)` core logic (no hardcoding downstream).
- [x] **#95** Implement hierarchical config resolution (file → defaults → constants).
- [x] **#96** Add validation hook: schema validation + type coercion + helpful errors.
- [x] **#97** Add validation hook: reject unknown/missing required keys.
- [x] **#98** Write positive test `test_config_manager.py` loading `setup.json`.
- [x] **#99** Write edge-case fixture: missing file, malformed JSON, wrong types.
- [x] **#100** Inject docstrings (why config-driven; cite Guidelines §7.2/§7.3).

### 2.E setup.json & friends
- [x] **#101** Author `config/setup.json` with `version`, `grid_size`, `max_moves`, `num_games`, `max_barriers`, `scoring{...}`.
- [x] **#102** Author `config/logging_config.json` (levels, file rotation, dispute log).
- [ ] **#103** Validation test: `setup.json` matches the typed model & immutable scoring.
- [ ] **#104** Edge fixture: 2×2 and 3×2 config variants for sanity stages (no code change).

### 2.F VersionGuard
- [x] **#105** Create `config/version_guard.py` skeleton.
- [x] **#106** Create `infra` version source `version.py` value `1.00` (code version).
- [x] **#107** Implement startup validation comparing code vs each config `version`.
- [x] **#108** Add validation hook: fail fast on version mismatch with clear message.
- [x] **#109** Write positive test `test_version_guard.py`.
- [x] **#110** Write edge-case fixture: mismatched config version raises.
- [x] **#111** Inject docstrings (Guidelines §8.1 versioning table).

### 2.G Secrets & git hygiene
- [x] **#112** Create `.env-example` with placeholders (LLM_API_KEY, GMAIL_*).
- [ ] **#113** Update `.gitignore` for `.env`, `credentials.json`, `token.json`, `*.key`, `*.pem`.
- [x] **#114** Implement `os.environ.get(...)` access pattern helper (no secrets in code).
- [ ] **#115** Secret-scan audit task: prove no keys/tokens in source.
- [ ] **#116** Phase-2 review: versioning, uv-only, ruff-clean, coverage gate active.

---

## PHASE 3 — The API Gatekeeper & Rate-Limiting Engine

### 3.A Companion PRD
- [x] **#117** Author [`PRD_gatekeeper.md`](./PRD_gatekeeper.md): FIFO, rate limits, retry, backpressure, criteria.

### 3.B RateLimiter (RateLimitMixin)
- [ ] **#118** Create `infra/rate_limiter.py` skeleton + typing.
- [ ] **#119** Implement per-minute/per-hour window counters (config-sourced).
- [ ] **#120** Implement `concurrent_max` tracking.
- [ ] **#121** Implement `allow()` decision + window reset/drain logic.
- [ ] **#122** Add validation hook: reject negative/zero limits from config.
- [ ] **#123** Write positive test `test_rate_limiter.py` (under limit passes).
- [ ] **#124** Write edge-case fixture: at-limit blocks; window reset re-allows.
- [ ] **#125** Inject docstrings.

### 3.C RetryPolicy (RetryMixin)
- [ ] **#126** Create `infra/retry.py` skeleton + typing.
- [ ] **#127** Implement retry with backoff (`max_retries`, `retry_after_seconds` from config).
- [ ] **#128** Distinguish transient vs permanent failures.
- [ ] **#129** Add validation hook: never retry non-idempotent permanent errors.
- [ ] **#130** Write positive test `test_retry.py` (succeeds on 2nd attempt).
- [ ] **#131** Write edge-case fixture: exhausts retries → surfaces controlled error.
- [ ] **#132** Inject docstrings.

### 3.D FIFO Queue & QueueMonitor
- [ ] **#133** Create `infra/queue_monitor.py` skeleton; define `QueueStatus` dataclass.
- [x] **#134** Implement bounded FIFO queue (`queue_max_depth` from config).
- [ ] **#135** Implement drain worker releasing on window reset.
- [x] **#136** Implement backpressure signal when queue full (no drop, no crash).
- [ ] **#137** Implement `get_queue_status()` (depth, stats).
- [x] **#138** Add validation hook: thread-safe access (lock / `queue.Queue`).
- [ ] **#139** Write positive test `test_queue_monitor.py` (enqueue/drain order preserved).
- [x] **#140** Write edge-case fixture: overflow raises backpressure, never crashes.
- [ ] **#141** Inject docstrings.

### 3.E ApiGatekeeper
- [x] **#142** Create `infra/gatekeeper.py` skeleton: `ApiGatekeeper(config: RateLimitConfig)`.
- [x] **#143** Implement `execute(api_call, *args, **kwargs)` composing rate-limit → queue → retry → log.
- [ ] **#144** Implement per-service routing (`default`, `llm`, `gmail`).
- [x] **#145** Add gatekeeper hook: structured logging of every call (monitoring).
- [ ] **#146** Add validation hook: forbid any path that bypasses `execute()`.
- [x] **#147** Write positive test `test_gatekeeper.py` (call passes through, logged).
- [ ] **#148** Write edge-case fixture: rate-limited call is queued then executed.
- [x] **#149** Write edge-case fixture: full queue → backpressure; transient failure → retried.
- [ ] **#150** Inject docstrings mirroring the Guidelines §5.1 interface.

### 3.F rate_limits.json
- [x] **#151** Author `config/rate_limits.json` (version `1.00`, services default/llm/gmail).
- [ ] **#152** Validation test: limits load into typed `RateLimitConfig`.
- [ ] **#153** Edge fixture: zero-depth queue & 1-rpm service behave correctly.
- [ ] **#154** Phase-3 review: 100 % external calls routed via gatekeeper (design check).

### 3.G Token Economics, Telemetry & Budget Tracker (NEW mechanism — see [`PRD_token_budget.md`](./PRD_token_budget.md))
- [x] **#387** Author [`PRD_token_budget.md`](./PRD_token_budget.md) (math baseline, telemetry contract, ceiling).
- [x] **#388** Add `token_budget` block to `config/setup.json` (rates, lifecycle budget, ceiling, warn_ratio, per-turn estimate) — versioned.
- [ ] **#389** Create `infra/cost_model.py`: pure `cost(P, C)` from config rates ($0.15/M in, $0.60/M out).
- [x] **#390** Create `infra/token_tracker.py` skeleton: thread-safe accumulators + `TelemetrySnapshot` typing.
- [x] **#391** Implement `record(service, prompt_tokens, completion_tokens, model, estimated)` with lock.
- [ ] **#392** Implement `status` computation (OK / WARN / CEILING_HIT) vs `warn_ratio`·ceiling and ceiling.
- [x] **#393** Implement atomic live-stream snapshot to `data/token_usage.json` (temp + `os.replace`).
- [ ] **#394** Implement `snapshot()` + startup reload of accumulators (crash-resumable).
- [x] **#395** Wire gatekeeper token-interception hook (`PRD_gatekeeper.md §4`) → `TokenTracker.record` (delegation only).
- [ ] **#396** Implement estimator fallback (`len/4`, `estimated=True`) when provider omits usage.
- [ ] **#397** Implement graceful ceiling enforcement: gatekeeper returns `BudgetExceeded` for billable LLM calls when `CEILING_HIT` (no crash; Gmail/mocked still allowed).
- [ ] **#398** SDK: inject `telemetry` block into `internal_game.json` and `bonus_report.json`.
- [ ] **#399** Ensure telemetry is **excluded** from the K3 `agreement_view` hash (`PRD_gmail_oauth.md §4.3`).
- [ ] **#400** Add validation hook: reject negative/garbage token counts (treat as 0 + log).
- [ ] **#401** Add validation hook: telemetry persistence failures are isolated (never break gameplay).
- [x] **#402** Write positive test `test_cost_model.py`: lifecycle 1.5M/180k ⇒ `0.333000` USD.
- [x] **#403** Write positive test `test_token_tracker.py`: 150×(850,90) ⇒ 127,500 / 13,500.
- [x] **#404** Write edge-case fixture: missing usage → estimate; ceiling-hit → `BudgetExceeded`; concurrent records → no lost updates; atomic-write integrity.
- [x] **#405** Inject Ruff-compliant docstrings across token modules.

---

## PHASE 4 — The SDK Layer Encapsulation

- [x] **#155** Create `sdk/sdk.py` skeleton: `CopThiefSDK` single-entrypoint class + typing.
- [x] **#156** Define SDK method signatures: `play_game`, `play_sub_game`, `decide_action`, `parse_message`, `build_internal_report`, `build_bonus_report`, `send_report`.
- [x] **#157** Implement delegation to Domain Services (no business logic in SDK).
- [x] **#158** Implement dependency injection of Gatekeeper, ConfigManager, Logger.
- [x] **#159** Add validation hook: SDK validates inputs before delegating.
- [x] **#160** Add gatekeeper hook: all external-facing SDK ops go through the gatekeeper.
- [x] **#161** Write positive test `test_sdk.py` (each method delegates correctly — mocked services).
- [x] **#162** Write edge-case fixture: invalid args raise clear SDK-level errors.
- [x] **#163** Write edge-case fixture: SDK callable by external consumer with no internal imports.
- [x] **#164** Inject docstrings: document the single entrypoint contract (Guidelines §4.1).
- [x] **#165** Wire `sdk/__init__.py` to export only `CopThiefSDK`.
- [x] **#166** Architecture test: assert GUI/CLI/servers import **only** the SDK (no domain imports).
- [x] **#167** Phase-4 review: confirm layered boundary SDK → Domain → Infrastructure.

---

## PHASE 5 — FastMCP Server A (The Cop Server & Tools)

### 5.A BaseMCPServer
- [x] **#168** Create `servers/base_server.py` skeleton: `BaseMCPServer` (FastMCP app, auth, SDK ref).
- [x] **#169** Implement common tool-registration template method.
- [x] **#170** Implement token-auth middleware hook (revocable token check).
- [x] **#171** Implement SDK delegation helper (servers carry no business logic).
- [x] **#172** Add validation hook: reject unauthenticated tool calls.
- [x] **#173** Write positive test `test_base_server.py` (registration + auth pass).
- [x] **#174** Write edge-case fixture: missing/invalid token rejected.
- [x] **#175** Inject docstrings.

### 5.B Cop tools
- [x] **#176** Create `servers/tools/cop_tools.py` skeleton + typing.
- [x] **#177** Implement `send_message(text)` tool (emit free-NL message).
- [x] **#178** Implement `receive_message(text)` tool (ingest opponent NL → belief update via SDK).
- [x] **#179** Implement `propose_action()` tool (move or place barrier via SDK strategy).
- [x] **#180** Implement `agree_on_report(report)` tool (mutual-agreement handshake).
- [x] **#181** Implement `trigger_report()` tool (end-of-game Gmail send via SDK).
- [x] **#182** Add validation hook: every tool validates payload; **no** numeric-protocol fields.
- [x] **#183** Add gatekeeper hook: tool LLM/Gmail calls go through the gatekeeper.
- [x] **#184** Write positive test `test_cop_tools.py` (each tool delegates to SDK — mocked).
- [x] **#185** Write edge-case fixture: malformed/empty message handled gracefully.
- [x] **#186** Write edge-case fixture: barrier proposal beyond quota rejected.
- [x] **#187** Inject docstrings per tool (Input/Output/Setup).

### 5.C CopServer
- [x] **#188** Create `servers/cop_server.py` skeleton subclassing `BaseMCPServer`.
- [x] **#189** Register Cop tools; bind config-driven port (no hardcoded port).
- [x] **#190** Implement local `localhost` HTTP run mode.
- [x] **#191** Add validation hook: startup version & config check.
- [x] **#192** Write positive test `test_cop_server.py` (boots, lists tools).
- [x] **#193** Write edge-case fixture: port from config; auth required.
- [x] **#194** Inject docstrings.
- [x] **#195** Smoke task: launch Cop server via `uv run` and hit a tool locally.

---

## PHASE 6 — FastMCP Server B (The Thief Server & Tools)

### 6.A Thief tools
- [x] **#196** Create `servers/tools/thief_tools.py` skeleton + typing.
- [x] **#197** Implement `send_message(text)` tool (free-NL, may include deception).
- [x] **#198** Implement `receive_message(text)` tool (NL → belief update via SDK).
- [x] **#199** Implement `propose_action()` tool (move only — no barrier capability).
- [x] **#200** Implement `agree_on_report(report)` tool (mutual-agreement handshake).
- [x] **#201** Add validation hook: reject any barrier action from the thief.
- [x] **#202** Add validation hook: ensure free-NL only (no numeric protocol).
- [x] **#203** Add gatekeeper hook: tool LLM calls routed through the gatekeeper.
- [x] **#204** Write positive test `test_thief_tools.py` (delegation — mocked).
- [x] **#205** Write edge-case fixture: thief barrier attempt rejected.
- [x] **#206** Write edge-case fixture: deceptive message still produces a legal move.
- [x] **#207** Inject docstrings per tool.

### 6.B ThiefServer
- [x] **#208** Create `servers/thief_server.py` skeleton subclassing `BaseMCPServer`.
- [x] **#209** Register Thief tools; bind config-driven port.
- [x] **#210** Implement local `localhost` HTTP run mode (distinct port from Cop).
- [x] **#211** Add validation hook: startup version & config check.
- [x] **#212** Write positive test `test_thief_server.py` (boots, lists tools).
- [x] **#213** Write edge-case fixture: distinct port, auth required.
- [x] **#214** Inject docstrings.
- [x] **#215** Smoke task: launch Thief server via `uv run`; verify Cop⇄Thief reachability locally.
- [x] **#216** Integration test: two servers exchange one free-NL message round-trip.
- [x] **#217** Phase-5/6 review: servers contain zero business logic (delegate to SDK only).

---

## PHASE 7 — The Client Orchestrator & LLM Natural-Language Parser

### 7.A LLM client adapters
- [x] **#218** Create `infra/llm_client.py` skeleton: single `LLMClient` interface + typing.
- [x] **#219** Create `infra/llm_cloud.py`: cloud API adapter (key from env).
- [x] **#220** Create `infra/llm_ollama.py`: local Ollama adapter (`127.0.0.1:11434`).
- [x] **#221** Implement provider selection from config (cloud / ollama / hybrid).
- [x] **#222** Add gatekeeper hook: all LLM calls via `gatekeeper.execute(...)`.
- [x] **#223** Add validation hook: timeouts/keys from config & env (no hardcoding).
- [x] **#224** Write positive test `test_llm_client.py` (adapter dispatch — mocked HTTP).
- [x] **#225** Write edge-case fixture: provider down → retry/backpressure path.
- [x] **#226** Inject docstrings (cite PRD §N-03 three approaches).

### 7.B NL Encoder
- [x] **#227** Create `domain/nl/encoder.py` skeleton + typing.
- [x] **#228** Implement state → free-NL message generation (no numeric coords).
- [x] **#229** Implement style/variety knobs from config (prompt templates in `prompts/`).
- [x] **#230** Add validation hook: assert output contains no machine-protocol tokens.
- [x] **#231** Write positive test `test_encoder.py`.
- [x] **#232** Write edge-case fixture: minimal 2×2 state still yields valid prose.
- [x] **#233** Inject docstrings.

### 7.C NL Parser
- [x] **#234** Create `domain/nl/parser.py` skeleton; define `BeliefUpdate` dataclass (dir, distance band, inferred barriers, confidence).
- [x] **#235** Implement LLM-prompted parse of unstructured text → `BeliefUpdate`.
- [x] **#236** Implement extraction of inferred barriers/walls from prose.
- [x] **#237** Implement confidence scoring of the parse.
- [x] **#238** Add gatekeeper hook: parser LLM call routed through gatekeeper.
- [x] **#239** Add validation hook: low-confidence/unparsable → safe default belief (never crash).
- [x] **#240** Write positive test `test_parser.py` (clear message → correct vector).
- [x] **#241** Write edge-case fixture: deceptive/ambiguous/empty message → defensive default.
- [x] **#242** Inject docstrings; finalize [`PRD_nl_protocol.md`](./PRD_nl_protocol.md).

### 7.D Strategy — BaseStrategy & Heuristic
- [x] **#243** Create `domain/strategy/base_strategy.py` skeleton (abstract `choose_action`).
- [x] **#244** Create `domain/strategy/heuristic_strategy.py` (Manhattan/Chebyshev pursuit & evasion).
- [x] **#245** Implement explicit **draw-avoidance** tie-break logic.
- [ ] **#246** Add validation hook: only return RulesEngine-legal actions.
- [ ] **#247** Write positive test `test_heuristic_strategy.py` (cop closes distance; thief opens it).
- [ ] **#248** Write edge-case fixture: stalemate scenario resolved without a draw.
- [ ] **#249** Inject docstrings.

### 7.E Strategy — Tabular Q-Learning
- [x] **#250** Create `domain/strategy/qlearning_strategy.py` skeleton; Q-table (states×actions).
- [x] **#251** Implement state encoding (positions + barriers → index) from config grid size.
- [x] **#252** Implement ε-greedy action selection (ε, decay from config).
- [x] **#253** Implement Bellman update `Q ← Q + α[r + γ·maxₐ′Q(s′,a′) − Q(s,a)]`.
- [x] **#254** Implement reward shaping (capture +, fall/penalty −, step cost) from config.
- [ ] **#255** Implement persistence/load of the Q-table (results dir).
- [ ] **#256** Add validation hook: clamp α,γ,ε to valid ranges from config.
- [x] **#257** Write positive test `test_qlearning_strategy.py` (single Bellman update math).
- [x] **#258** Write edge-case fixture: terminal state → no bootstrap (`done` path).
- [ ] **#259** Write edge-case fixture: convergence on a tiny 2×2 toy MDP.
- [x] **#260** Inject docstrings; finalize [`PRD_rl_qtable.md`](./PRD_rl_qtable.md).

### 7.F BaseAgent / Cop / Thief agents
- [ ] **#261** Create `domain/agents/base_agent.py` (template method `take_turn`: perceive→decide→act→message).
- [ ] **#262** Create `domain/agents/cop_agent.py` (uses strategy + barrier capability + reporting).
- [ ] **#263** Create `domain/agents/thief_agent.py` (uses strategy; evasion + deception messaging).
- [ ] **#264** Add validation hook: agents emit only legal actions and free-NL messages.
- [ ] **#265** Write positive test `test_base_agent.py` / `test_cop_agent.py` / `test_thief_agent.py`.
- [ ] **#266** Write edge-case fixture: agent given garbage observation → safe behavior.
- [ ] **#267** Inject docstrings.

### 7.G Orchestrator
- [ ] **#268** Create `orchestrator/message_router.py` (carry free-NL Cop⇄Thief over MCP).
- [ ] **#269** Implement routing with structured logging of each message.
- [x] **#270** Create `orchestrator/game_loop.py`: `GameLoopController` turn loop via SDK.
- [x] **#271** Implement sub-game loop (≤`max_moves`, terminal detection, scoring).
- [ ] **#272** Implement full-game loop (`num_games`=6, accumulate totals).
- [ ] **#273** Implement **technical-loss** handling: void & re-run until 6 valid sub-games.
- [ ] **#274** Create `orchestrator/report_trigger.py` (fire reporter at end-of-game).
- [x] **#275** Add gatekeeper hook: orchestrator never calls LLM/Gmail directly (only via SDK/gatekeeper).
- [x] **#276** Add validation hook: enforce one action per turn; deterministic state.
- [x] **#277** Write positive test `test_game_loop.py` (scripted full sub-game completes).
- [ ] **#278** Write edge-case fixture: injected technical fault triggers re-run path.
- [x] **#279** Write edge-case fixture: max-moves reached → thief win recorded.
- [x] **#280** Inject docstrings.

### 7.H Structured Logger
- [ ] **#281** Create `infra/logger.py` (`StructuredLogger`/`LoggingMixin`) from `logging_config.json`.
- [ ] **#282** Implement dispute-proof event log (move, message, decision, outcome, hash).
- [ ] **#283** Add validation hook: redact secrets from logs.
- [ ] **#284** Write positive test `test_logger.py`.
- [ ] **#285** Write edge-case fixture: log rotation & no-secret-leak assertion.
- [ ] **#286** Inject docstrings.

### 7.I Reporting & Agreement
- [ ] **#287** Create `domain/reporting/base_report.py` (`BaseReport` + `SerializationMixin`, version stamp).
- [ ] **#288** Create `domain/reporting/internal_report.py` matching the internal JSON schema (group_name, students, github_repo, cop_mcp_url, thief_mcp_url, timezone, sub_games, totals{cop,thief}).
- [ ] **#289** Create `domain/reporting/bonus_report.py` matching the bonus schema (report_type, groups, 2× github, 4× mcp_url, students_group_1/2, sub_games, totals_by_group, bonus_claim, mutual_agreement).
- [x] **#290** Create `orchestrator/reconcile.py`: `reconcile_agreement` (byte-identical outcome; mismatch ⇒ both lose 0/0).
- [x] **#291** Implement agreement via shared log hash / canonical serialization. *(`canonical_hash` = treaty §D pipeline.)*
- [ ] **#292** Add validation hook: schema validation of both report types.
- [ ] **#293** Add validation hook: refuse to send if `mutual_agreement` is false.
- [ ] **#294** Write positive test `test_internal_report.py` / `test_bonus_report.py` (schema match).
- [ ] **#295** Write positive test `test_agreement.py` (matching reports → true).
- [ ] **#296** Write edge-case fixture: divergent reports → agreement false → send blocked (K3).
- [ ] **#297** Write edge-case fixture: bonus tie → 5/5; win/lose → 10/7; average over series.
- [ ] **#298** Inject docstrings (cite PRD §3.5 bonus rules).
- [ ] **#299** Phase-7 review: NL-only protocol verified end-to-end; SDK boundary intact.

---

## PHASE 8 — OAuth2 Desktop Client & Gmail API JSON Reporter

### 8.A Companion PRD
- [x] **#300** Author [`PRD_gmail_oauth.md`](./PRD_gmail_oauth.md) (desktop OAuth flow, scopes, JSON-only body, criteria).

### 8.B Google Cloud setup (manual, documented)
- [x] **#301** Create Google Cloud project; open Google Auth Platform.
- [x] **#302** Configure audience = External; add the Gmail test account as a **Test User**.
- [x] **#303** Enable the Gmail API for the project.
- [x] **#304** Under Data access, add scopes `gmail.modify` (+ `calendar` per guide, unused).
- [x] **#305** Create an OAuth client of type **Desktop**; download JSON.
- [x] **#306** Rename to `credentials.json` in project root; confirm it is git-ignored.
- [ ] **#307** Document the whole flow with screenshots in `assets/` and README.

### 8.C OAuth flow
- [ ] **#308** Create `auth/oauth_flow.py` skeleton + typing.
- [x] **#309** Implement desktop OAuth2 flow (`credentials.json` → `token.json`).
- [x] **#310** Implement token refresh + revoke handling.
- [x] **#311** Add validation hook: no passwords anywhere; tokens only; token git-ignored.
- [ ] **#312** Write positive test `test_oauth_flow.py` (token build — mocked Google libs).
- [ ] **#313** Write edge-case fixture: expired token refresh; revoked token → re-auth.
- [ ] **#314** Inject docstrings (cite PRD §N-01 token-over-password rationale).

### 8.D Gmail Reporter
- [ ] **#315** Create `auth/gmail_reporter.py` skeleton + typing.
- [ ] **#316** Implement build of a MIME message with **JSON-only** body (no free text).
- [ ] **#317** Implement send via Gmail API to `rmisegal+uoh26b@gmail.com`.
- [ ] **#318** Implement "exactly one email at end of game" guard.
- [ ] **#319** Add gatekeeper hook: Gmail send routed via `gatekeeper.execute(...)` (gmail service limits).
- [ ] **#320** Add validation hook: assert body is valid JSON & matches report schema before send.
- [ ] **#321** Write positive test `test_gmail_reporter.py` (send invoked — mocked service).
- [ ] **#322** Write edge-case fixture: free-text in body → rejected by guard.
- [ ] **#323** Write edge-case fixture: send retried under transient failure via gatekeeper.
- [ ] **#324** Inject docstrings.
- [ ] **#325** Integration test: end-of-game → Cop triggers reporter (mocked Gmail) once.
- [ ] **#326** Dry-run task: one real send from a private test inbox before the examiner address.
- [ ] **#327** Phase-8 review: secrets clean, JSON-only enforced, single-send verified.

### 8.E SubmissionSafetyGuard — SEC-03 burner loopback interlock (`src/cop_thief/reporting/guard.py`)
- [x] **#406** Create `reporting/guard.py` skeleton: `SubmissionSafetyGuard` + typing; safety-interlock boolean (`burner_verified`).
- [x] **#407** Implement the interlock gate: refuse the live Examiner send until a successful burner→burner dry-run has flipped the boolean.
- [x] **#408** Add validation hook: burner & examiner addresses are config-sourced (`reporting.burner_email` / `reporting.examiner_email`); fail-closed when interlock is false.
- [x] **#409** Write positive test `test_guard.py` (interlock true → live allowed; false → blocked with clear error).
- [x] **#410** Edge-case fixture (double-arm idempotent; reset) + inject Ruff-compliant docstrings.

### 8.F Observer GUI — UI-01 native tkinter window (`src/cop_thief/gui/window.py`)
- [x] **#411** Create `gui/window.py` skeleton (stdlib `tkinter`, zero extra deps) + typing; omitted from coverage.
- [x] **#412** Implement the left 5×5 (config-driven) `Canvas` layout with cell grid.
- [x] **#413** Implement agent/barrier rendering: **Blue = Cop, Red = Thief, Black = active Barriers**, re-drawn from `DecPomdpGameState`.
- [x] **#414** Implement the right-hand scrolling text feed live-streaming the NL prose banter.
- [x] **#415** Implement the thread-safe queue consumer (`queue.Queue` + `after()` polling) — the GUI never blocks the game loop.
- [x] **#416** Wire an observer hook so each `execute_single_turn_cycle` tick pushes `(state, prose)` onto the GUI queue.
- [x] **#417** Write a positive visual unit test (headless-safe): push a state+prose, assert canvas items/colours and feed text; skip gracefully when no display is available.
- [x] **#418** Inject Ruff-compliant docstrings; confirm ≤150 LOC (split renderer if needed).

---

## PHASE 9 — Sanity-Check Progression Run (2×2, 3×3, 4×4, 5×5)

### 9.A Stage 1 — 2×2
- [ ] **#328** Set config `grid_size=[2,2]`; confirm **no code change** required.
- [ ] **#329** Run full 6-sub-game game locally (two servers) at 2×2.
- [ ] **#330** Verify the message **pipeline** end-to-end and basic integration.
- [ ] **#331** Verify both reports agree (K3) at 2×2.
- [ ] **#332** Integration test `test_stage1_2x2.py`; capture logs to `results/`.

### 9.B Stage 2 — 3×3 / 3×2
- [ ] **#333** Set config `grid_size=[3,3]` (and `[3,2]` variant).
- [ ] **#334** Run full game; verify coordination-mechanism convergence.
- [ ] **#335** Tune hyper-parameters (α, γ, ε; turn timing) via config only.
- [ ] **#336** Exercise failure detection (inject a void sub-game, confirm re-run).
- [ ] **#337** Integration test `test_stage2_3x3.py`; record metrics.

### 9.C Stage 3 — 4×4 / 4×3
- [ ] **#338** Set config `grid_size=[4,4]` (and `[4,3]` variant).
- [ ] **#339** Configure starting distance to exceed the vision band (stress partial observability).
- [ ] **#340** Run full game; verify NL parsing copes with greater uncertainty.
- [ ] **#341** Verify agreement still holds under harder conditions.
- [ ] **#342** Integration test `test_stage3_4x4.py`; record metrics.

### 9.D Stage 4 — 5×5
- [ ] **#343** Set config `grid_size=[5,5]`, `max_moves=25`, `num_games=6`, `max_barriers=5`.
- [ ] **#344** Run the final full game; record full per-sub-game outcomes & totals.
- [ ] **#345** Generate Q-Learning **learning curves** into `assets/`.
- [ ] **#346** Generate capture-frequency **heatmaps** & per-stage **win-rate** charts.
- [ ] **#347** Produce **sensitivity analysis** (α/γ/ε) in `notebooks/`.
- [ ] **#348** Integration test `test_stage4_5x5.py`; full-game analysis.
- [ ] **#349** Verify Cop emits the JSON-only report via Gmail API at game end.
- [ ] **#350** Confirm coverage ≥85 %, `ruff` clean, all gates green across the suite.
- [ ] **#351** Author/update scientific `README.md`: Dec-POMDP tuple, orchestration-challenge analysis, graphs.
- [ ] **#352** Phase-9 review: all four stages pass in order; results archived.

### 9.E Burner Loopback Dry-Run — SEC-03 execution
- [ ] **#419** Register the burner sandbox address `mcp.marl.telemetry@gmail.com` as `reporting.burner_email` (config) and an OAuth Test User.
- [ ] **#420** Execute the burner→burner JSON handshake dry-run via the Gmail API (`mcp.marl.telemetry@gmail.com` → itself).
- [ ] **#421** Verify Gmail-API formatting/auth on the loopback and assert the `SubmissionSafetyGuard` interlock flips to `burner_verified=True`.
- [ ] **#422** Only after a successful loopback, enable the live Examiner send path (`rmisegal+uoh26b@gmail.com`).
- [ ] **#423** Integration test `test_burner_loopback.py` (mocked Gmail): live send blocked pre-loopback, allowed post-loopback; archive the dry-run log to `results/`.

---

## PHASE 10 — Public Cloud Tunneling (ngrok/Localtonet) & Bonus Inter-Group Matchmaking Prep

### 10.A Cloud deployment of MCP servers
- [ ] **#353** Choose cloud target (e.g. Prefect Cloud) for the two MCP servers.
- [ ] **#354** Provision the **Cop** public MCP URL.
- [ ] **#355** Provision the **Thief** public MCP URL.
- [ ] **#356** Implement token authentication on both public endpoints.
- [ ] **#357** Implement token **revoke** capability (security N-02).
- [ ] **#358** Configure outbound-only HTTPS (hybrid LLM model; no inbound ports).
- [ ] **#359** Validation test: public endpoints reject calls without a valid token.
- [ ] **#360** Smoke test: orchestrator drives a full game against the cloud URLs.

### 10.A (CLOUD-02) Public HTTPS Tunnel provisioning & security assertions
- [ ] **#424** Install/configure **Cloudflare Tunnel** (`cloudflared`) — or **Localtonet** as fallback — for two persistent HTTPS endpoints.
- [ ] **#425** Map `https://cop.team-domain.trycloudflare.com` → `localhost:8001` and `https://thief.team-domain.trycloudflare.com` → `localhost:8002`.
- [ ] **#426** Set `config/setup.json` `servers.cop.local_port=8001` / `servers.thief.local_port=8002` to align with the tunnel mapping.
- [ ] **#427** Enforce revocable bearer tokens on both endpoints via `SecurityMiddleware` (constant-time `compare_digest`).
- [ ] **#428** Security assertion test: a call with a missing/invalid token is rejected (fail-closed).
- [ ] **#429** Security assertion test: HTTPS endpoint reachable; a rotated token invalidates prior access (revocation works).
- [ ] **#430** Document the tunnel provisioning + token-revoke runbook in `README.md` / `assets/`.

### 10.B Tunneling options (when exposing a local LLM/server)
- [ ] **#361** Implement ngrok path: Traffic Policy / Basic Auth + Authorization header.
- [ ] **#362** Document Localtonet alternative (public tunnel to `127.0.0.1:11434` + HTTP auth).
- [ ] **#363** Document Nginx reverse-proxy path (SSL termination, htpasswd, Certbot, firewall).
- [ ] **#364** Add firewall rules (UFW/nftables) protecting the Ollama port.
- [ ] **#365** Security review: confirm no API keys/IPs exposed; only MCP servers reachable.
- [ ] **#366** Edge fixture: tunnel auth failure → access denied (no leakage).

### 10.C Bonus matchmaking prep
- [ ] **#367** Implement bonus role-rotation orchestration: first 3 sub-games A-cop vs B-thief; last 3 B-cop vs A-thief.
- [ ] **#368** Implement four-URL wiring (both groups' cop & thief servers).
- [ ] **#369** Implement bonus report assembly (`bonus_report.py`) with `totals_by_group` & `bonus_claim`.
- [ ] **#370** Implement separate-but-identical reporting: each group sends its own email, same result.
- [ ] **#371** Implement bonus scoring: 10 / 7 / 5 per series; average over valid series.
- [ ] **#372** Implement mismatch handling: divergent reports → series cancelled → 0/0.
- [ ] **#373** Write positive test `test_bonus_series.py` (full bilateral series, agreement true).
- [ ] **#374** Write edge-case fixture: report mismatch → both score 0 for that series.
- [ ] **#375** Write edge-case fixture: tie series → 5/5; multi-series average (e.g. 10 & 7 → 8.5).
- [ ] **#376** Inter-group dry-run: exchange tokens, run one full cloud series with a partner group.
- [ ] **#377** Inject docstrings across bonus modules; record inter-group protocol agreement (non-enforceable).

### 10.D Final consolidation & submission
- [ ] **#378** Prompt-engineering log: populate `prompts/` (context, goals, sample outputs, iterations).
- [ ] **#379** Token-cost analysis table (input/output tokens, cost per model) in README/notebook.
- [ ] **#380** Finalize `README.md` (install, usage, config guide, screenshots, license & credits).
- [ ] **#381** Verify mandatory docs: `PRD.md`, `PLAN.md`, `TODO.md`, all per-mechanism PRDs present.
- [ ] **#382** Run final checklist (Guidelines §17): SDK boundary, gatekeeper, ≤150 LOC, docstrings.
- [ ] **#383** Confirm `uv.lock` + `pyproject.toml` committed; `uv run` drives every tool.
- [ ] **#384** Confirm `ruff check` = 0 and `pytest --cov` ≥85 %.
- [ ] **#385** Tidy Git history; tag release `v1.00`; add deployment instructions, license, credits.
- [ ] **#386** Final acceptance: 4-stage sanity passed, mutually-agreed JSON report emailed, bonus prepped.

---

---

## MILESTONE 5 — Decentralized Match Play, Live UI & Inter-Group Competition

See [`PLAN.md` §10](./PLAN.md) and [`RULES_AND_AGREEMENTS.md`](./RULES_AND_AGREEMENTS.md).

### Phase A — Local real match + live UI (strategy iteration loop)
- [x] **#431** Create `cop_thief/app.py`: one asyncio process hosting Cop MCP (:8001) + Thief MCP (:8002) + UI SSE (:8800) + orchestrator (coverage-omit entrypoint).
- [x] **#432** Create `orchestrator/match.py` `MatchOrchestrator`: real turn loop, **thief-first**, deterministic NL-move apply, terminal via `evaluate_terminal_condition`.
- [x] **#433** Stream every turn to the in-process `broadcast` bus AND append to `data/game_audit.jsonl` (live UI shows C/T/B + moves).
- [x] **#434** Create `domain/strategy/roster.py` `AgentRoster`: 3 strategy variants per role; **game = 3 matches** (agent *i* vs agent *i*).
- [x] **#435** Deterministic NL move parse↔apply parity helper (both sides resolve identical board) reusing `[INTENT]` + direction vocabulary.
- [x] **#436** Unit tests: thief-first ordering, 3-match game tally, deterministic apply parity, roster wiring.
- [x] **#437** Live smoke: `app.py` control panel verified end-to-end (servers/tunnels up, status API, URLs populated, game renders on `:8800`).

### Phase B — Inter-group (defender / challenger + mutual agreement)
- [x] **#438** Defender tool `request_move(observation_prose, auth_token) -> move_prose` on each MCP server (token-guarded, hard-armored).
- [x] **#439** Challenger transport: `RemoteMoveClient` (MCP `Client` over `/sse`) drives a full 6-sub-game game; live app challenges its own endpoints (mirror), partner tunnel URL is a drop-in target.
- [x] **#440** Per-side authoritative state + transmission audit log (dispute evidence per RULES §5/§6).
- [x] **#441** SHA-256 mutual-agreement reconcile (`reconcile_agreement`); mismatch → 0/0 `both_lose`. *(Multi-round Diplomat negotiation still optional.)*
- [x] **#442** End-of-series Gmail report (burner default; `--production-drop` to examiner) reusing `treaty_runner`.
- [x] **#443** Security assertions: token required on all tools; rotation invalidates; injection rejected + logged. *(Opponent-facing law codified in INTER_GROUP_TREATY_SPEC.md v1.2 §F + §E tool contract + §G token exchange.)*
- [ ] **#444** Integration test: full local two-roster series with deterministic agreed reports (mocked LLM transport).
- [x] **#444b** Interactive cross-host challenge entrypoint (`cop_thief.challenge`): prompts opponent URLs/tokens/email, preflights their `request_move`, plays 6 sub-games with per-leg routing (our role local, theirs over MCP), emails the `bonus_game` report. `ChallengeRunner` unit-tested.
- [x] **#444c** One-command host: `cop_thief.serve` runs MCP servers + tunnels together (no orphan-tunnel 530s); servers exposed via streamable-HTTP `/mcp` (matches opponents); switchboard shares full `/mcp/` URLs.
- [x] **#444d** **Web control panel** (`cop_thief.app`): single command boots servers + tunnels + panel UI (`:8800`). Live node status (`NodeState` + `/api/status`), our shareable URLs/tokens with copy, an opponent challenge form (`/api/challenge` → worker thread → cross-host game + email), and the live 5×5 TV — all in the browser. Verified end-to-end (servers/tunnels up, URLs populated).

### Phase C — Actual strategy in live play (priority #3)
- [x] **#445** `[INTENT: BARRIER]` move-language (`encode_barrier` / `parse_intent`); `apply_prose` walls the **Cop's own current cell** (ex06 §4.3); intent read only from the bracketed tag (spoof-proof).
- [x] **#446** **Barrier rule corrected to §4.3** — `is_barrier_legal` now allows only the Cop's current cell (was wrongly Chebyshev ≤ 1 / adjacent). Removed the illegal adjacent auto-seal heuristic (`barrier_target`); the geometry resolver no longer auto-emits barriers. *Smart current-cell barrier USE (herding → `thief_trapped`) is owned by the strategy layer → #448.*
- [x] **#447** Slice 3b — `StrategyResolver` per-variant wiring via the `variant` index; variant labels surface in the report + UI banner. *(Superseded by #448: the live policy is now the minimax engine, not an epsilon-greedy Q-policy; tabular Q is the documented baseline.)*
- [x] **#449** **Adaptive strategy** — risk/expectimax knob in `minimax.py` (pessimism: minimax↔expectimax); online `OpponentModel` (`opponent.py`) sets pessimism from the opponent's observed rational-rate; variants carry a `risk`. **Random openings** (§4.2) via `geometry.random_start_positions` + `game.start_mode`/`random_seed`, seeded so both groups reproduce the opening. 109 tests green.
- [x] **#448** **Angel–Devil strategy engine** ([`STRATEGY.md`](./STRATEGY.md)) — game-theoretic alpha-beta minimax (`minimax.py`) over the zero-sum Markov game; Conway Devil barriers in the search action set with a flood-fill *containment* evaluation (`features.py`/`evaluation.py`); advanced self-play RL weight learning (`selfplay.py`). `StrategyResolver` now drives 3 minimax variant profiles; draws structurally avoided. Captures in ~8 turns; tabular Q kept as the documented baseline.

### Milestone 6 — Pre-game readiness (remaining cycles; see AS-BUILT RECONCILIATION above)
- [x] **#456** Barrier-move fix (ex06 §4.3): a barrier is impassable to BOTH, so the Cop can't wall its own cell and stay on it. `apply_action`/`is_barrier_legal` now wall the **vacated** cell and step the Cop to an adjacent free cell; `encode_barrier`/`apply_prose` carry the step direction; minimax offers one barrier-move per legal step. Invariant (cop never on a barrier) sim-verified. Docs: RULES §3, treaty §A/§B, PRD STRAT-01, match_setup/RULES.txt.
- [x] **#457** Barrier-move turn accounting: the wall + step is **one turn** (one `apply_action` → `turn_counter +1`, role flips, −1 barrier) — already correct in code; locked with a test and stated explicitly in RULES §3 / treaty §B / PRD STRAT-01 / match_setup/RULES.txt.
- [x] **#450** README: Screenshots section (control panel, live board, leg transition — `screenshots/`), terminal boot/switchboard block, and a **Token budget & cost** table (config-driven; lifecycle ≈ $0.333, live ≈ $0 via local minimax). Covers #307/#351/#379/#380/#430.
- [x] **#451** Active injection counter-measure — `RetaliationLadder` (`warfare.py`): escalating counter-payload (silent → notice → counter-strike → stacked override) appended to our move only after a *logged* opponent offence; wired in `ChallengeRunner._retaliating`. Never alters our engine move / carries no direction word (no Spite Trap). Docs: PRD SEC-05, RULES §6.3, treaty §F deterrent.
- [x] **#452** Dispute log archive — `reporting/archive.py` `DisputeArchive`: per-game immutable bundle (`data/archive/`) of every transmission + board snapshot + `board_sha256` + hostility verdict + report, sealed by a `bundle_sha256` (tamper-evident). Wired in `ChallengeRunner` (records each turn, seals at game end, surfaces hash in the report). Docs: PRD SEC-06, RULES §5.
- [x] **#453** §9.2 `bonus_game` schema — `reporting/bonus_report.py`: `canonical_sub_games` (treaty-§D entries so both groups hash identically) + `build_bonus_report` (exact §9.2 envelope: groups, both github, four `mcp_url_*`, students, `totals_by_group`, agreement hash, `mutual_agreement`, `bonus_claim`). Closes #288/#289/#294/#369; agreed-reports integration (#444) tested. Fed real metadata from the match-setup exchange form at game time.
- [x] **#455** Match-setup pack — `match_setup/`: `RULES.txt` (ready, opponent-facing summary of the treaty), `OUR_DETAILS__UNFILLED.txt` (what we send them) and `OPPONENT_DETAILS__UNFILLED.txt` (what we collect). URLs/tokens are placeholders (they change per cloudflared restart); filenames marked `__UNFILLED` → fill + drop the suffix at game time.
- [ ] **#458** Re-do Gmail/Google Cloud after the old reporting account was banned — runbook at `match_setup/GMAIL_SETUP.txt`. Code: `GmailApiReporter` sender is now **config-driven** (`reporting.burner_email`); config burner set to a `CHANGEME` placeholder. Manual Google steps + new `credentials.json` + `rm token.json` are done at setup time.
- [x] **#459** Per-match terms toggle — a candidate opponent negotiated barriers-off + fixed corners + deterministic replays, so the engine grew config-driven knobs: **deterministic tournament mode** (`game.deterministic_moves`: move = pure fn(observation), greedy minimax, no exploration/history → byte-agreeing replays), a **barriers on/off** toggle (`game.barriers_enabled`), and **fixed-corner openings** (`start_mode="fixed"` + `fixed_start`). Guard `_ALWAYS_ALLOW` is now the config burner (was the banned hardcoded address).
- [x] **#461** That opponent withdrew → reverted `config/setup.json` to our **standing defaults**: `start_mode="random"`, `barriers_enabled=true` (Cop's 5 barrier-moves back), `deterministic_moves=false` (adaptive risk variants + opponent model), `fixed_start=null`. Deleted their match files and scrubbed the opponent name from code/tests/docs. KEPT the generic per-match knobs (re-usable for the next group, exercised by tests) and #460's both-ways email.
- [x] **#460** Guaranteed post-game email both ways. When WE challenge, the challenge/panel flow emails (as before). When the OPPONENT drives the official series (treaty §8), `cop_thief.report <sub_games.json>` builds the exact §9.2 bonus_game report from the **confirmed agreed array** and emails it (digest == both sides') — so our report always goes out regardless of who ran the loop.
- [x] **#462** Barrier rule change — a barrier and a move are now **separate turns** (supersedes #456/#457). On a `[INTENT: BARRIER]` turn the Cop walls **one adjacent free cell** (never its own or the Thief's) and **stays in place** — it does NOT also move; placing a wall spends one of the ≤25 moves + one of the ≤5 barriers, then the opponent moves, and moving is its own later turn. `apply_action` walls `target` and keeps `cop_pos`; `is_barrier_legal` = adjacent King step ∧ not cop/thief cell; `encode_barrier`/`apply_prose` say "walls the cell to its <dir>"; minimax offers `(PLACE_BARRIER, adjacent_free_cell)`. Docs: RULES §3, treaty §A/§B, PRD STRAT-01/03 + action-set, README, match_setup/RULES.txt. Tests updated (barriers, domain, bedrock, engine).
- [x] **#463** Report schemas aligned to ex06 §9 exactly. (a) §9.2 `bonus_claim` is now the spec **dict** `{group: int}` (was the string `"up_to_10_points"`). (b) New `build_internal_report` emits the exact **§9.1 Internal Game JSON** (`group_name`/`students`/`github_repo`/`cop_mcp_url`/`thief_mcp_url`/`timezone`/`sub_games`/`totals{cop,thief}`); the panel auto-email now sends THIS (the mandatory, JSON-only report). (c) Group identity is config-driven — new `GroupConfig` (`config.group`: group_name/github_repo/students); `cop_thief.report` (§9.2) defaults our side from config. The inter-group §9.2 stays the deliberate `cop_thief.report` path (needs the agreed array + group strings). The rich `ChallengeRunner` report is unchanged (internal working object for UI/archive).
- [x] **#464** End-of-game auto-email is now the exact ex06 **§9.2 `bonus_game`** envelope (the inter-group game we actually play), replacing the §9.1 stub. `build_bonus_from_report` maps the played game → treaty-§D canonical `sub_games`, pulls group_1/group_2 identity + opponent URLs from config, and takes **our** two MCP URLs **dynamically** from the live tunnels (`STATE.cop_url`/`thief_url`, config fallback) since we hold no permanent URL. `mutual_agreement` carries from the run (`None` until digests are reconciled; flip to `true` via `cop_thief.report` after confirming equal). Opponent identity (Mohamad-Salih, their github/students/MCP URLs) + our students now in `config`.
- [x] **#465** Email sends **regardless of who drives**. New passive `InboundGameObserver` (wired into both MCP servers by the app via `dual_mcp_host`): when the OPPONENT drives (calls our `request_move`), it accrues every observation, segments it into sub-games (role flip / turn reset), infers each outcome from the turns observed, and after the opponent goes idle (~45 s) auto-emails the **same** §9.2 `bonus_game` report (`build_bonus_from_report`, dynamic our-URLs) to `reporting.burner_email` (test inbox now; examiner for the real run). When WE drive, the panel still emails (our servers aren't called, so no double-send). Tests inject the emailer; factories take `observer=None` (no-op) so the suite stays quiet.
- [x] **#466** `request_move` no longer crashes on a non-numeric `variant` (opponent sent `"standard"`); `_variant_index` coerces int/digit-string/label and falls back to variant 0.
- [x] **#467** Transport resilience so the series COMPLETES (no partial reports). A dropped/refused opponent connection on a single move — even the last move of sub-game 6 — used to abort the whole game and send no email. `RemoteMoveClient` now retries each move up to 4× with a fresh connection (2 s backoff); a transient blip recovers and all 6 sub-games finish, then the full §9.2 email goes out. Only a genuinely-down opponent (all attempts fail) surfaces the error.
- [ ] **#454** Real inter-group game run vs a live opponent (fill the `match_setup/` forms first; may need adjustments to accommodate them).

*End of TODO. **Status of record = AS-BUILT RECONCILIATION (v2.0) above** + the PRD §4.1 requirements
(all implemented) + the 109-test suite. The granular #1–#430 WBS is the original plan, historical and
superseded where noted. Update continuously (Guidelines §2.5).*
