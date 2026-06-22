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

## PHASE 1 — Core Domain, Grid Mechanics & State Machine (Dec-POMDP)

### 1.A constants.py
- [ ] **#1** Create `src/cop_thief/constants.py` skeleton with module docstring & typing imports.
- [ ] **#2** Define `Direction` Enum (8 directions + STAY) with `(dr, dc)` vectors.
- [ ] **#3** Define `AgentRole` Enum (`COP`, `THIEF`) and `ActionType` Enum (`MOVE`, `PLACE_BARRIER`).
- [ ] **#4** Define `SubGameOutcome` Enum (`COP_WINS`, `THIEF_WINS`, `VOID_TECHNICAL`).
- [ ] **#5** Add immutable physical/math constants (default vision band labels, tie-break order).
- [ ] **#6** Write positive unit test `tests/unit/test_constants.py` asserting enum members & vectors.
- [ ] **#7** Add edge-case fixture: assert no duplicate direction vectors, STAY = (0,0).
- [ ] **#8** Inject Ruff-compliant docstrings explaining *why* each enum exists.

### 1.B Cell & Grid
- [ ] **#9** Create `domain/grid.py` skeleton; define `Cell` dataclass (row, col) with typing.
- [ ] **#10** Implement `Cell` equality, hashing, and neighbor computation.
- [ ] **#11** Define `Grid` class skeleton (rows, cols sourced from config, not literals).
- [ ] **#12** Implement `Grid.in_bounds(cell)` core logic.
- [ ] **#13** Implement `Grid.neighbors(cell, include_diagonal=True)` core logic.
- [ ] **#14** Add validation hook: reject non-positive grid dimensions (raise `ValueError`).
- [ ] **#15** Write positive test `test_grid.py`: bounds & neighbors on a 5×5.
- [ ] **#16** Write edge-case fixture: 1×1, 2×2, and non-square (3×2) grids.
- [ ] **#17** Write edge-case fixture: corner/edge cells have correct reduced neighbor sets.
- [ ] **#18** Inject docstrings (Input/Output/Setup per building-block format).

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
- [ ] **#114** Implement `os.environ.get(...)` access pattern helper (no secrets in code).
- [ ] **#115** Secret-scan audit task: prove no keys/tokens in source.
- [ ] **#116** Phase-2 review: versioning, uv-only, ruff-clean, coverage gate active.

---

## PHASE 3 — The API Gatekeeper & Rate-Limiting Engine

### 3.A Companion PRD
- [ ] **#117** Author [`PRD_gatekeeper.md`](./PRD_gatekeeper.md): FIFO, rate limits, retry, backpressure, criteria.

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
- [ ] **#134** Implement bounded FIFO queue (`queue_max_depth` from config).
- [ ] **#135** Implement drain worker releasing on window reset.
- [ ] **#136** Implement backpressure signal when queue full (no drop, no crash).
- [ ] **#137** Implement `get_queue_status()` (depth, stats).
- [ ] **#138** Add validation hook: thread-safe access (lock / `queue.Queue`).
- [ ] **#139** Write positive test `test_queue_monitor.py` (enqueue/drain order preserved).
- [ ] **#140** Write edge-case fixture: overflow raises backpressure, never crashes.
- [ ] **#141** Inject docstrings.

### 3.E ApiGatekeeper
- [ ] **#142** Create `infra/gatekeeper.py` skeleton: `ApiGatekeeper(config: RateLimitConfig)`.
- [ ] **#143** Implement `execute(api_call, *args, **kwargs)` composing rate-limit → queue → retry → log.
- [ ] **#144** Implement per-service routing (`default`, `llm`, `gmail`).
- [ ] **#145** Add gatekeeper hook: structured logging of every call (monitoring).
- [ ] **#146** Add validation hook: forbid any path that bypasses `execute()`.
- [ ] **#147** Write positive test `test_gatekeeper.py` (call passes through, logged).
- [ ] **#148** Write edge-case fixture: rate-limited call is queued then executed.
- [ ] **#149** Write edge-case fixture: full queue → backpressure; transient failure → retried.
- [ ] **#150** Inject docstrings mirroring the Guidelines §5.1 interface.

### 3.F rate_limits.json
- [x] **#151** Author `config/rate_limits.json` (version `1.00`, services default/llm/gmail).
- [ ] **#152** Validation test: limits load into typed `RateLimitConfig`.
- [ ] **#153** Edge fixture: zero-depth queue & 1-rpm service behave correctly.
- [ ] **#154** Phase-3 review: 100 % external calls routed via gatekeeper (design check).

### 3.G Token Economics, Telemetry & Budget Tracker (NEW mechanism — see [`PRD_token_budget.md`](./PRD_token_budget.md))
- [ ] **#387** Author [`PRD_token_budget.md`](./PRD_token_budget.md) (math baseline, telemetry contract, ceiling).
- [ ] **#388** Add `token_budget` block to `config/setup.json` (rates, lifecycle budget, ceiling, warn_ratio, per-turn estimate) — versioned.
- [ ] **#389** Create `infra/cost_model.py`: pure `cost(P, C)` from config rates ($0.15/M in, $0.60/M out).
- [ ] **#390** Create `infra/token_tracker.py` skeleton: thread-safe accumulators + `TelemetrySnapshot` typing.
- [ ] **#391** Implement `record(service, prompt_tokens, completion_tokens, model, estimated)` with lock.
- [ ] **#392** Implement `status` computation (OK / WARN / CEILING_HIT) vs `warn_ratio`·ceiling and ceiling.
- [ ] **#393** Implement atomic live-stream snapshot to `data/token_usage.json` (temp + `os.replace`).
- [ ] **#394** Implement `snapshot()` + startup reload of accumulators (crash-resumable).
- [ ] **#395** Wire gatekeeper token-interception hook (`PRD_gatekeeper.md §4`) → `TokenTracker.record` (delegation only).
- [ ] **#396** Implement estimator fallback (`len/4`, `estimated=True`) when provider omits usage.
- [ ] **#397** Implement graceful ceiling enforcement: gatekeeper returns `BudgetExceeded` for billable LLM calls when `CEILING_HIT` (no crash; Gmail/mocked still allowed).
- [ ] **#398** SDK: inject `telemetry` block into `internal_game.json` and `bonus_report.json`.
- [ ] **#399** Ensure telemetry is **excluded** from the K3 `agreement_view` hash (`PRD_gmail_oauth.md §4.3`).
- [ ] **#400** Add validation hook: reject negative/garbage token counts (treat as 0 + log).
- [ ] **#401** Add validation hook: telemetry persistence failures are isolated (never break gameplay).
- [ ] **#402** Write positive test `test_cost_model.py`: lifecycle 1.5M/180k ⇒ `0.333000` USD.
- [ ] **#403** Write positive test `test_token_tracker.py`: 150×(850,90) ⇒ 127,500 / 13,500.
- [ ] **#404** Write edge-case fixture: missing usage → estimate; ceiling-hit → `BudgetExceeded`; concurrent records → no lost updates; atomic-write integrity.
- [ ] **#405** Inject Ruff-compliant docstrings across token modules.

---

## PHASE 4 — The SDK Layer Encapsulation

- [ ] **#155** Create `sdk/sdk.py` skeleton: `CopThiefSDK` single-entrypoint class + typing.
- [ ] **#156** Define SDK method signatures: `play_game`, `play_sub_game`, `decide_action`, `parse_message`, `build_internal_report`, `build_bonus_report`, `send_report`.
- [ ] **#157** Implement delegation to Domain Services (no business logic in SDK).
- [ ] **#158** Implement dependency injection of Gatekeeper, ConfigManager, Logger.
- [ ] **#159** Add validation hook: SDK validates inputs before delegating.
- [ ] **#160** Add gatekeeper hook: all external-facing SDK ops go through the gatekeeper.
- [ ] **#161** Write positive test `test_sdk.py` (each method delegates correctly — mocked services).
- [ ] **#162** Write edge-case fixture: invalid args raise clear SDK-level errors.
- [ ] **#163** Write edge-case fixture: SDK callable by external consumer with no internal imports.
- [ ] **#164** Inject docstrings: document the single entrypoint contract (Guidelines §4.1).
- [ ] **#165** Wire `sdk/__init__.py` to export only `CopThiefSDK`.
- [ ] **#166** Architecture test: assert GUI/CLI/servers import **only** the SDK (no domain imports).
- [ ] **#167** Phase-4 review: confirm layered boundary SDK → Domain → Infrastructure.

---

## PHASE 5 — FastMCP Server A (The Cop Server & Tools)

### 5.A BaseMCPServer
- [ ] **#168** Create `servers/base_server.py` skeleton: `BaseMCPServer` (FastMCP app, auth, SDK ref).
- [ ] **#169** Implement common tool-registration template method.
- [ ] **#170** Implement token-auth middleware hook (revocable token check).
- [ ] **#171** Implement SDK delegation helper (servers carry no business logic).
- [ ] **#172** Add validation hook: reject unauthenticated tool calls.
- [ ] **#173** Write positive test `test_base_server.py` (registration + auth pass).
- [ ] **#174** Write edge-case fixture: missing/invalid token rejected.
- [ ] **#175** Inject docstrings.

### 5.B Cop tools
- [ ] **#176** Create `servers/tools/cop_tools.py` skeleton + typing.
- [ ] **#177** Implement `send_message(text)` tool (emit free-NL message).
- [ ] **#178** Implement `receive_message(text)` tool (ingest opponent NL → belief update via SDK).
- [ ] **#179** Implement `propose_action()` tool (move or place barrier via SDK strategy).
- [ ] **#180** Implement `agree_on_report(report)` tool (mutual-agreement handshake).
- [ ] **#181** Implement `trigger_report()` tool (end-of-game Gmail send via SDK).
- [ ] **#182** Add validation hook: every tool validates payload; **no** numeric-protocol fields.
- [ ] **#183** Add gatekeeper hook: tool LLM/Gmail calls go through the gatekeeper.
- [ ] **#184** Write positive test `test_cop_tools.py` (each tool delegates to SDK — mocked).
- [ ] **#185** Write edge-case fixture: malformed/empty message handled gracefully.
- [ ] **#186** Write edge-case fixture: barrier proposal beyond quota rejected.
- [ ] **#187** Inject docstrings per tool (Input/Output/Setup).

### 5.C CopServer
- [ ] **#188** Create `servers/cop_server.py` skeleton subclassing `BaseMCPServer`.
- [ ] **#189** Register Cop tools; bind config-driven port (no hardcoded port).
- [ ] **#190** Implement local `localhost` HTTP run mode.
- [ ] **#191** Add validation hook: startup version & config check.
- [ ] **#192** Write positive test `test_cop_server.py` (boots, lists tools).
- [ ] **#193** Write edge-case fixture: port from config; auth required.
- [ ] **#194** Inject docstrings.
- [ ] **#195** Smoke task: launch Cop server via `uv run` and hit a tool locally.

---

## PHASE 6 — FastMCP Server B (The Thief Server & Tools)

### 6.A Thief tools
- [ ] **#196** Create `servers/tools/thief_tools.py` skeleton + typing.
- [ ] **#197** Implement `send_message(text)` tool (free-NL, may include deception).
- [ ] **#198** Implement `receive_message(text)` tool (NL → belief update via SDK).
- [ ] **#199** Implement `propose_action()` tool (move only — no barrier capability).
- [ ] **#200** Implement `agree_on_report(report)` tool (mutual-agreement handshake).
- [ ] **#201** Add validation hook: reject any barrier action from the thief.
- [ ] **#202** Add validation hook: ensure free-NL only (no numeric protocol).
- [ ] **#203** Add gatekeeper hook: tool LLM calls routed through the gatekeeper.
- [ ] **#204** Write positive test `test_thief_tools.py` (delegation — mocked).
- [ ] **#205** Write edge-case fixture: thief barrier attempt rejected.
- [ ] **#206** Write edge-case fixture: deceptive message still produces a legal move.
- [ ] **#207** Inject docstrings per tool.

### 6.B ThiefServer
- [ ] **#208** Create `servers/thief_server.py` skeleton subclassing `BaseMCPServer`.
- [ ] **#209** Register Thief tools; bind config-driven port.
- [ ] **#210** Implement local `localhost` HTTP run mode (distinct port from Cop).
- [ ] **#211** Add validation hook: startup version & config check.
- [ ] **#212** Write positive test `test_thief_server.py` (boots, lists tools).
- [ ] **#213** Write edge-case fixture: distinct port, auth required.
- [ ] **#214** Inject docstrings.
- [ ] **#215** Smoke task: launch Thief server via `uv run`; verify Cop⇄Thief reachability locally.
- [ ] **#216** Integration test: two servers exchange one free-NL message round-trip.
- [ ] **#217** Phase-5/6 review: servers contain zero business logic (delegate to SDK only).

---

## PHASE 7 — The Client Orchestrator & LLM Natural-Language Parser

### 7.A LLM client adapters
- [ ] **#218** Create `infra/llm_client.py` skeleton: single `LLMClient` interface + typing.
- [ ] **#219** Create `infra/llm_cloud.py`: cloud API adapter (key from env).
- [ ] **#220** Create `infra/llm_ollama.py`: local Ollama adapter (`127.0.0.1:11434`).
- [ ] **#221** Implement provider selection from config (cloud / ollama / hybrid).
- [ ] **#222** Add gatekeeper hook: all LLM calls via `gatekeeper.execute(...)`.
- [ ] **#223** Add validation hook: timeouts/keys from config & env (no hardcoding).
- [ ] **#224** Write positive test `test_llm_client.py` (adapter dispatch — mocked HTTP).
- [ ] **#225** Write edge-case fixture: provider down → retry/backpressure path.
- [ ] **#226** Inject docstrings (cite PRD §N-03 three approaches).

### 7.B NL Encoder
- [ ] **#227** Create `domain/nl/encoder.py` skeleton + typing.
- [ ] **#228** Implement state → free-NL message generation (no numeric coords).
- [ ] **#229** Implement style/variety knobs from config (prompt templates in `prompts/`).
- [ ] **#230** Add validation hook: assert output contains no machine-protocol tokens.
- [ ] **#231** Write positive test `test_encoder.py`.
- [ ] **#232** Write edge-case fixture: minimal 2×2 state still yields valid prose.
- [ ] **#233** Inject docstrings.

### 7.C NL Parser
- [ ] **#234** Create `domain/nl/parser.py` skeleton; define `BeliefUpdate` dataclass (dir, distance band, inferred barriers, confidence).
- [ ] **#235** Implement LLM-prompted parse of unstructured text → `BeliefUpdate`.
- [ ] **#236** Implement extraction of inferred barriers/walls from prose.
- [ ] **#237** Implement confidence scoring of the parse.
- [ ] **#238** Add gatekeeper hook: parser LLM call routed through gatekeeper.
- [ ] **#239** Add validation hook: low-confidence/unparsable → safe default belief (never crash).
- [ ] **#240** Write positive test `test_parser.py` (clear message → correct vector).
- [ ] **#241** Write edge-case fixture: deceptive/ambiguous/empty message → defensive default.
- [ ] **#242** Inject docstrings; finalize [`PRD_nl_protocol.md`](./PRD_nl_protocol.md).

### 7.D Strategy — BaseStrategy & Heuristic
- [ ] **#243** Create `domain/strategy/base_strategy.py` skeleton (abstract `choose_action`).
- [ ] **#244** Create `domain/strategy/heuristic_strategy.py` (Manhattan/Chebyshev pursuit & evasion).
- [ ] **#245** Implement explicit **draw-avoidance** tie-break logic.
- [ ] **#246** Add validation hook: only return RulesEngine-legal actions.
- [ ] **#247** Write positive test `test_heuristic_strategy.py` (cop closes distance; thief opens it).
- [ ] **#248** Write edge-case fixture: stalemate scenario resolved without a draw.
- [ ] **#249** Inject docstrings.

### 7.E Strategy — Tabular Q-Learning
- [ ] **#250** Create `domain/strategy/qlearning_strategy.py` skeleton; Q-table (states×actions).
- [ ] **#251** Implement state encoding (positions + barriers → index) from config grid size.
- [ ] **#252** Implement ε-greedy action selection (ε, decay from config).
- [ ] **#253** Implement Bellman update `Q ← Q + α[r + γ·maxₐ′Q(s′,a′) − Q(s,a)]`.
- [ ] **#254** Implement reward shaping (capture +, fall/penalty −, step cost) from config.
- [ ] **#255** Implement persistence/load of the Q-table (results dir).
- [ ] **#256** Add validation hook: clamp α,γ,ε to valid ranges from config.
- [ ] **#257** Write positive test `test_qlearning_strategy.py` (single Bellman update math).
- [ ] **#258** Write edge-case fixture: terminal state → no bootstrap (`done` path).
- [ ] **#259** Write edge-case fixture: convergence on a tiny 2×2 toy MDP.
- [ ] **#260** Inject docstrings; finalize [`PRD_rl_qtable.md`](./PRD_rl_qtable.md).

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
- [ ] **#270** Create `orchestrator/game_loop.py`: `GameLoopController` turn loop via SDK.
- [ ] **#271** Implement sub-game loop (≤`max_moves`, terminal detection, scoring).
- [ ] **#272** Implement full-game loop (`num_games`=6, accumulate totals).
- [ ] **#273** Implement **technical-loss** handling: void & re-run until 6 valid sub-games.
- [ ] **#274** Create `orchestrator/report_trigger.py` (fire reporter at end-of-game).
- [ ] **#275** Add gatekeeper hook: orchestrator never calls LLM/Gmail directly (only via SDK/gatekeeper).
- [ ] **#276** Add validation hook: enforce one action per turn; deterministic state.
- [ ] **#277** Write positive test `test_game_loop.py` (scripted full sub-game completes).
- [ ] **#278** Write edge-case fixture: injected technical fault triggers re-run path.
- [ ] **#279** Write edge-case fixture: max-moves reached → thief win recorded.
- [ ] **#280** Inject docstrings.

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
- [ ] **#290** Create `domain/reporting/agreement.py`: `AgreementReconciler` (byte-identical outcome).
- [ ] **#291** Implement agreement via shared log hash / canonical serialization.
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
- [ ] **#300** Author [`PRD_gmail_oauth.md`](./PRD_gmail_oauth.md) (desktop OAuth flow, scopes, JSON-only body, criteria).

### 8.B Google Cloud setup (manual, documented)
- [ ] **#301** Create Google Cloud project; open Google Auth Platform.
- [ ] **#302** Configure audience = External; add the Gmail test account as a **Test User**.
- [ ] **#303** Enable the Gmail API for the project.
- [ ] **#304** Under Data access, add scopes `gmail.modify` (+ `calendar` per guide, unused).
- [ ] **#305** Create an OAuth client of type **Desktop**; download JSON.
- [ ] **#306** Rename to `credentials.json` in project root; confirm it is git-ignored.
- [ ] **#307** Document the whole flow with screenshots in `assets/` and README.

### 8.C OAuth flow
- [ ] **#308** Create `auth/oauth_flow.py` skeleton + typing.
- [ ] **#309** Implement desktop OAuth2 flow (`credentials.json` → `token.json`).
- [ ] **#310** Implement token refresh + revoke handling.
- [ ] **#311** Add validation hook: no passwords anywhere; tokens only; token git-ignored.
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

*End of TODO — 405 numbered tasks across the 10 sequential engineering phases (incl. the token-budget mechanism, #387–#405).*
*Update this file continuously during development (Guidelines §2.5, step 6).*
