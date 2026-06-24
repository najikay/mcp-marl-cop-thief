# PLAN — Technical Architecture & Execution Plan
## Dual AI Agent Conversation via MCP Servers — Dec-POMDP Cop & Thief Chase

| Field | Value |
|-------|-------|
| Project | `marl-cop-thief` |
| Document version | 1.00 |
| Depends on | [`PRD.md`](./PRD.md) (approved) |
| Drives | [`TODO.md`](./TODO.md) |
| Standard | Dr. Segal *Guidelines for Professional Software Excellence v3.00* |

> **As-built note (v2.0):** Sections 1–9 are the original design. The **authoritative as-built
> architecture is [§10 — Architecture v2 (Decentralized Match Play)](#10-architecture-v2--decentralized-match-play--single-app-topology-milestone-5)**,
> plus the [`STRATEGY.md`](./STRATEGY.md) engine. Where they differ, §10 / STRATEGY win: the
> `RulesEngine`+Mixin tree (§2.2) and the fine-grained file tree (§3) were **consolidated** into
> `domain/` (`state.py`, `grid.py`, `geometry.py`, `move_language.py`), the strategy is **minimax +
> Conway Angel–Devil + self-play RL** (not tabular-Q-in-live), and the topology is the single-command
> control panel (servers + tunnels + UI). See `TODO.md` → *AS-BUILT RECONCILIATION*.

---

## 1. System Architecture — C4 Model

### 1.1 Level 1 — System Context
```
                         ┌──────────────────────────────┐
   ┌──────────┐  free-NL │   marl-cop-thief  (System)   │  OAuth2 + Gmail API
   │ Rival    │◀────────▶│  Two autonomous AI agents     │────────────▶ ┌────────────┐
   │ Group's  │  (bonus) │  play a Dec-POMDP pursuit and │   JSON-only  │  Examiner   │
   │ MCP URLs │          │  report the result            │   email      │  (Gmail)    │
   └──────────┘          └───────────────┬──────────────┘              └────────────┘
                                         │  HTTPS (tool calls / chat completion)
                                         ▼
                                 ┌───────────────┐
                                 │  LLM Provider  │  Cloud API (OpenAI / Anthropic /
                                 │  (Gatekept)    │  Gemini)  OR  local Ollama
                                 └───────────────┘
```
**Actors:** the Examiner (human grader via Gmail), rival groups (bonus), the LLM provider.
**External systems:** Gmail API, the LLM endpoint, the cloud/tunneling platform.

### 1.2 Level 2 — Containers
| Container | Responsibility | Tech |
|-----------|----------------|------|
| **Cop MCP Server** | Exposes Cop tools (send/receive NL message, propose move/barrier, agree-on-report). No business logic — delegates to SDK. | FastMCP, HTTP(S) |
| **Thief MCP Server** | Exposes Thief tools (send/receive NL message, propose move, agree-on-report). Delegates to SDK. | FastMCP, HTTP(S) |
| **Client Orchestrator** | The game engine: turn loop, message routing, LLM querying, rule enforcement, logging, report trigger. Owns the LLM client. | Python, `uv` |
| **API Gatekeeper** | Single chokepoint for all external calls (LLM, Gmail): FIFO queue, rate limit, retry, monitor. | Python |
| **SDK Layer** | Single entrypoint to all domain logic for every consumer (servers, CLI, GUI, tests). | Python |
| **Domain Core** | Grid state machine, rules, scoring, strategy, NL parsing, report builders. | Python |
| **Gmail Reporter** | OAuth2 desktop flow + Gmail-API JSON-only send. | google-api-python-client |
| **Submission Safety Guard** (SEC-03) | Interlock enforcing a successful **burner→burner loopback** dry-run before the live Examiner address is ever contacted. | Python |
| **Config Store** | Versioned JSON/YAML: game params, rate limits, logging. | `config/` |
| **Observer GUI** (UI-01) | Native **zero-dependency `tkinter`** window: left 5×5 `Canvas` (Blue=Cop, Red=Thief, Black=Barriers) + right scrolling NL-banter feed; fed by a **thread-safe queue**, never blocks the loop. | `tkinter` (stdlib) |
| **Public Tunnels** (CLOUD-02) | Two persistent HTTPS URLs (Cloudflare `cloudflared` / Localtonet) → local FastMCP, revocable-token secured. | cloudflared / localtonet |

**Routing of the LLM (3 supported approaches; default = #1, hybrid for local dev = #3):**
1. **Cloud API** — orchestrator calls a cloud LLM with an API key (stable, fast, cheap on short msgs).
2. **Exposed local Ollama** — Ollama on `:11434` behind ngrok/Localtonet/Nginx with auth (SSL, htpasswd).
3. **Hybrid** — Ollama + orchestrator stay local; only the MCP servers go to cloud; outbound-only HTTPS.

### 1.3 Level 3 — Components (inside the Orchestrator + Domain Core)
```
Orchestrator
 ├─ GameLoopController      (turn arbiter; delegates to SDK only)
 ├─ MessageRouter          (carries free-NL text Cop⇄Thief over MCP)
 └─ ReportTrigger          (fires at end-of-game)
SDK (single entrypoint: CopThiefSDK)
 ├─ play_sub_game / play_game
 ├─ decide_action / parse_message
 ├─ build_internal_report / build_bonus_report
 └─ send_report
Domain Core
 ├─ Grid / Cell / BoardStateMachine
 ├─ RulesEngine (MovementMixin, BarrierMixin, CaptureMixin, TurnMixin)
 ├─ ScoringEngine (config-sourced, immutable values)
 ├─ Strategy (BaseStrategy → HeuristicStrategy, QLearningStrategy)
 ├─ NLProtocol (Encoder: state→NL; Parser: NL→vector/barriers)
 └─ ReportBuilder (internal + bonus schemas) + AgreementReconciler
Infrastructure
 ├─ Gatekeeper (FIFO, RateLimiter, RetryPolicy, QueueMonitor)
 ├─ LLMClient (cloud/Ollama adapters behind one interface)
 ├─ GmailReporter (OAuth2 desktop + send)
 ├─ ConfigManager + VersionGuard
 └─ StructuredLogger
```

### 1.4 Level 4 — Code (key contracts)
```python
class CopThiefSDK:                       # the ONLY entrypoint for all consumers
    def play_game(self, grid_size, num_games) -> GameReport: ...
    def decide_action(self, belief, role) -> Action: ...
    def parse_message(self, text, role) -> BeliefUpdate: ...
    def send_report(self, report) -> SendResult: ...

class ApiGatekeeper:                      # wraps ALL external calls
    def __init__(self, config: RateLimitConfig): ...
    def execute(self, api_call, *args, **kwargs): ...
    def get_queue_status(self) -> QueueStatus: ...
```

---

## 2. OOP & DRY Strategy (keep every file ≤ 150 LOC)

### 2.1 Base Classes
| Base class | Purpose |
|------------|---------|
| `BaseAgent` | Shared agent lifecycle (perceive → decide → act → report); template method `take_turn()`. |
| `BaseStrategy` | Abstract `choose_action(belief) -> Action`; subclassed by heuristic & Q-learning. |
| `BaseMCPServer` | Common FastMCP wiring (tool registration, auth, SDK delegation); Cop/Thief subclass it. |
| `BaseReport` | Shared serialization/validation; internal & bonus reports subclass it. |
| `BaseConfigModel` | Versioned, validated config object base. |

### 2.2 Mixins (single concern, independently testable — Guidelines §4.2)
| Mixin | Single concern |
|-------|----------------|
| `MovementMixin` | 8-direction movement + edge clamping. |
| `BarrierMixin` | Barrier placement, quota, impassability. |
| `CaptureMixin` | Same-cell capture detection. |
| `TurnMixin` | Turn order / alternation arbiter. |
| `ScoringMixin` | Apply the immutable scoring matrix. |
| `RetryMixin` | Transient-failure retry (used by gatekeeper). |
| `RateLimitMixin` | Window counters + backpressure decision. |
| `SerializationMixin` | `to_json` / `from_json` with version stamping. |
| `LoggingMixin` | Structured, dispute-proof event logging. |

> Mixin rules enforced: each provides exactly **one** concern, mixins do **not** override each
> other's methods, and each is **independently unit-tested**.

### 2.3 Template Methods & DRY rules
- `BaseAgent.take_turn()` is a **template method**; subclasses fill `decide()`/`message()`.
- Repeated `try/except` around external IO → wrapped once in the **Gatekeeper** (no duplication).
- Any logic appearing in ≥2 files → extracted to a shared module; values → `constants.py` or config.

### 2.4 SDK Interface (concrete)
`CopThiefSDK` is the single import surface. GUI, CLI, MCP tool handlers, and tests call **only** the
SDK; none of them contain business logic. The SDK delegates to Domain Services, which delegate to
Infrastructure (DB/file IO/external APIs) — strictly layered (Guidelines §4.1).

---

## 3. Complete File Tree (highly granular, every file ≤150 LOC)
```
marl-cop-thief/
├── src/
│   └── cop_thief/
│       ├── __init__.py
│       ├── constants.py                 # immutable constants (Enums, directions)
│       ├── main.py                      # CLI entrypoint (uv run)
│       ├── sdk/
│       │   ├── __init__.py
│       │   └── sdk.py                    # CopThiefSDK — single entrypoint
│       ├── domain/
│       │   ├── __init__.py
│       │   ├── grid.py                   # Grid + Cell
│       │   ├── board_state.py            # BoardStateMachine
│       │   ├── rules/
│       │   │   ├── __init__.py
│       │   │   ├── rules_engine.py
│       │   │   ├── movement_mixin.py
│       │   │   ├── barrier_mixin.py
│       │   │   ├── capture_mixin.py
│       │   │   └── turn_mixin.py
│       │   ├── scoring.py                # ScoringEngine + ScoringMixin
│       │   ├── agents/
│       │   │   ├── __init__.py
│       │   │   ├── base_agent.py
│       │   │   ├── cop_agent.py
│       │   │   └── thief_agent.py
│       │   ├── strategy/
│       │   │   ├── __init__.py
│       │   │   ├── base_strategy.py
│       │   │   ├── heuristic_strategy.py
│       │   │   └── qlearning_strategy.py # tabular Q (Bellman, ε-greedy)
│       │   ├── nl/
│       │   │   ├── __init__.py
│       │   │   ├── encoder.py            # state → natural language
│       │   │   └── parser.py             # natural language → vectors/barriers
│       │   └── reporting/
│       │       ├── __init__.py
│       │       ├── base_report.py
│       │       ├── internal_report.py    # internal game JSON schema
│       │       ├── bonus_report.py       # inter-group bonus JSON schema
│       │       └── agreement.py          # mutual-agreement reconciler
│       ├── orchestrator/
│       │   ├── __init__.py
│       │   ├── game_loop.py              # GameLoopController
│       │   ├── message_router.py
│       │   └── report_trigger.py
│       ├── servers/
│       │   ├── __init__.py
│       │   ├── base_server.py            # BaseMCPServer (FastMCP wiring)
│       │   ├── cop_server.py             # Cop FastMCP server + tools
│       │   ├── thief_server.py           # Thief FastMCP server + tools
│       │   └── tools/
│       │       ├── __init__.py
│       │       ├── cop_tools.py
│       │       └── thief_tools.py
│       ├── infra/
│       │   ├── __init__.py
│       │   ├── gatekeeper.py             # ApiGatekeeper
│       │   ├── rate_limiter.py           # RateLimitMixin impl
│       │   ├── retry.py                  # RetryMixin impl
│       │   ├── queue_monitor.py
│       │   ├── llm_client.py             # cloud/Ollama adapter interface
│       │   ├── llm_cloud.py
│       │   ├── llm_ollama.py
│       │   └── logger.py                 # StructuredLogger / LoggingMixin
│       ├── auth/
│       │   ├── __init__.py
│       │   ├── oauth_flow.py             # OAuth2 desktop flow
│       │   └── gmail_reporter.py         # Gmail-API JSON-only send
│       ├── reporting/
│       │   ├── __init__.py
│       │   └── guard.py                  # SubmissionSafetyGuard (SEC-03 burner loopback interlock)
│       ├── config/
│       │   ├── __init__.py
│       │   ├── config_manager.py
│       │   ├── version_guard.py
│       │   └── models.py                 # BaseConfigModel + typed models
│       └── gui/                          # optional, omitted from coverage
│           ├── __init__.py
│           ├── app.py
│           └── window.py                 # UI-01 tkinter Observer Canvas (5x5 grid + NL feed, thread-safe queue)
├── tests/
│   ├── conftest.py                       # shared fixtures
│   ├── unit/                             # mirrors src/ structure
│   │   └── ...                           # test_<file>.py per module
│   └── integration/
│       └── ...                           # test_<feature>.py (end-to-end, sanity stages)
├── docs/
│   ├── PRD.md
│   ├── PLAN.md
│   ├── TODO.md
│   ├── PRD_rl_qtable.md
│   ├── PRD_nl_protocol.md
│   ├── PRD_gatekeeper.md
│   └── PRD_gmail_oauth.md
├── config/
│   ├── setup.json                        # grid_size, max_moves, num_games, max_barriers, scoring
│   ├── rate_limits.json                  # gatekeeper limits (versioned)
│   └── logging_config.json
├── data/
├── results/
├── assets/                               # graphs, screenshots, diagrams
├── notebooks/                            # analysis (learning curves, sensitivity)
├── prompts/                              # prompt engineering log
├── README.md                            # scientific README (Dec-POMDP model + analysis)
├── pyproject.toml                       # build, deps, ruff, coverage
├── uv.lock
├── .env-example
└── .gitignore
```

---

## 4. Dec-POMDP Natural-Language Protocol Design
**Goal:** agents exchange only free natural language; each side's LLM converts text → grid action.
Full detail in [`PRD_nl_protocol.md`](./PRD_nl_protocol.md).

### 4.1 Pipeline
```
State (private)  ──Encoder──▶  free-NL message  ──MCP tool──▶  opponent server
opponent message ──LLM Parser──▶ BeliefUpdate {est_opponent_dir, est_distance, inferred_barriers, confidence}
BeliefUpdate ──Strategy──▶ Action {MOVE(dir) | PLACE_BARRIER}  ──RulesEngine.validate──▶ apply
```

### 4.2 Encoder (state → NL)
Produces human-style, non-numeric-protocol prose (e.g. *"I'm hugging the eastern wall and just
sealed the lane to my south — you won't squeeze through there"*). Style/variety is config-tunable;
**no** machine-coordinate fields are emitted.

### 4.3 Parser (NL → actionable vector)
The receiving LLM extracts, from unstructured text, a structured **BeliefUpdate**:
estimated opponent direction (one of 8), estimated distance band, inferred barrier cells, and a
confidence score. The parser is **defensive**: on low confidence or unparsable text it returns a
safe default (explore toward last-known region) rather than an illegal move.

### 4.4 Validation
Every parsed/decided action passes `RulesEngine.validate(action, state)` before being applied:
in-bounds, not into a barrier/wall, barrier quota respected. Invalid → graceful fallback (never crash).

---

## 5. Error Handling & Backpressure Strategy (API Gatekeeper)
Full detail in [`PRD_gatekeeper.md`](./PRD_gatekeeper.md).

### 5.1 Principles (Guidelines §5)
- **No external call bypasses the gatekeeper.** All LLM and Gmail calls go through `execute()`.
- Rate limits are **read from `config/rate_limits.json`** (versioned), never hardcoded.
- On limit reached → enqueue to a **FIFO** queue (do **not** drop).
- All calls are logged for monitoring.

### 5.2 Backpressure
- Bounded FIFO with `queue_max_depth` from config.
- On full queue → raise **backpressure** signal to callers (slow down), **never crash**.
- Drain worker releases requests as rate windows reset.
- Transient failures → `RetryPolicy` (`max_retries`, `retry_after_seconds` from config) with backoff.

### 5.3 Example config (`config/rate_limits.json`)
```json
{
  "version": "1.00",
  "rate_limits": {
    "services": {
      "default":  { "requests_per_minute": 30, "requests_per_hour": 500,
                    "concurrent_max": 5, "retry_after_seconds": 30, "max_retries": 3,
                    "queue_max_depth": 100 },
      "llm":      { "requests_per_minute": 20, "concurrent_max": 3, "max_retries": 3,
                    "queue_max_depth": 200 },
      "gmail":    { "requests_per_minute": 5,  "concurrent_max": 1, "max_retries": 5,
                    "queue_max_depth": 20 }
    }
  }
}
```

### 5.4 Failure taxonomy & responses
| Failure | Layer | Response |
|---------|-------|----------|
| Rate-limit hit | Gatekeeper | Enqueue (FIFO), backpressure |
| Queue full | Gatekeeper | Signal backpressure to caller; no crash |
| Transient 5xx / timeout | RetryPolicy | Retry with backoff up to `max_retries` |
| LLM unparsable output | NL Parser | Defensive default BeliefUpdate |
| Illegal proposed move | RulesEngine | Reject + safe fallback |
| Sub-game technical abort | Orchestrator | Mark void; re-run to reach 6 valid sub-games |
| OAuth token expired | GmailReporter | Refresh; if revoked, re-auth flow |

---

## 6. Architecture Decision Records (ADRs)
| ADR | Decision | Rationale | Alternatives |
|-----|----------|-----------|--------------|
| ADR-1 | FastMCP for both servers | Brief mandates MCP; FastMCP ready-made | Raw MCP SDK |
| ADR-2 | LLM owned by orchestrator, not the MCP server | Matches brief §5.2 (LLM not stored in server) | LLM inside server |
| ADR-3 | Default LLM = cloud API; hybrid for local dev | Stability, cost, no machine exposure | Exposed local Ollama |
| ADR-4 | Tabular Q-Learning (if RL used) | Brief recommends; no GPU/NN needed | DQN/heuristic-only |
| ADR-5 | OAuth2 desktop + token over passwords | Security (N-01); revocable, scoped | SMTP+password |
| ADR-6 | Single gatekeeper for LLM **and** Gmail | DRY; one backpressure/retry path | Per-service handling |
| ADR-7 | Config-driven grid size | Sanity progression with zero code change | Hardcoded per stage |

---

## 7. Networking, Deployment & Security Plan
- **Local:** Cop & Thief servers on `localhost`, distinct ports, HTTP; orchestrator connects locally.
- **Cloud:** promote both servers to public URLs via **Cloudflare tunnels** (`switchboard.py`); **two URLs per group**
  (cop, thief), token-authenticated and revocable; outbound-only HTTPS for the hybrid LLM model.
- **Tunneling (if exposing local):** ngrok Traffic Policy / Basic Auth, Localtonet, or Nginx
  (SSL termination + htpasswd + Certbot + firewall on the Ollama port).
- **CLOUD-02 — Persistent public HTTPS tunnels (chosen approach):** two durable tunnels front the
  two local FastMCP servers, each guarded by a revocable bearer token (`COP_MCP_TOKEN` /
  `THIEF_MCP_TOKEN`) validated by `SecurityMiddleware` (constant-time `compare_digest`):

  | Public HTTPS URL | → local target | Server | Token env |
  |------------------|----------------|--------|-----------|
  | `https://cop.team-domain.trycloudflare.com`   | `localhost:8001` | Cop server   | `COP_MCP_TOKEN`   |
  | `https://thief.team-domain.trycloudflare.com` | `localhost:8002` | Thief server | `THIEF_MCP_TOKEN` |

  Provision via **Cloudflare Tunnel** (`cloudflared tunnel --url http://localhost:8001`) or
  **Localtonet** as the fallback. Traffic is outbound-only (no inbound ports opened); HTTPS is
  terminated by the tunnel provider; tokens are revoked by rotating the env value and restarting.
  Security assertion tests confirm: (a) calls without a valid token are rejected, (b) the HTTPS
  endpoint is reachable, (c) a rotated token invalidates prior access. *(Local ports 8001/8002 align
  with the tunnel mapping; `config/setup.json` `servers.*.local_port` is set accordingly at deploy.)*
- **Secrets:** `.env` only (git-ignored); `.env-example` committed; `credentials.json`/`token.json`
  git-ignored; periodic key rotation; least-privilege scopes (`gmail.modify`).

---

## 8. Testing & Quality Plan (TDD)
- **Red-Green-Refactor** for every module; tests written **before/with** code.
- `tests/unit/` mirrors `src/`; `tests/integration/` covers the 4 sanity stages end-to-end.
- Shared fixtures in `conftest.py`; **mock** all external IO (LLM, Gmail, files).
- Coverage ≥85 % (`fail_under = 85`); GUI & `main.py` omitted from coverage.
- `ruff check` = 0 violations (`select = E,F,W,I,N,UP,B,C4,SIM`).
- Versioning validated at startup (code + config = `1.00`).

---

## 9. Research & Visualization Plan (for README scientific section)
- Q-Learning **learning curves**; **sensitivity analysis** over `α`, `γ`, `ε`.
- Heatmaps of capture frequency by start distance; per-stage win-rate bar charts.
- Token-cost breakdown table; orchestration-challenge discussion (NL ambiguity, agreement).
- Analysis notebook in `notebooks/`; assets in `assets/`.

---

## 10. Architecture v2 — Decentralized Match Play & Single-App Topology (Milestone 5)

This supersedes the implicit "self-play only" runner. Governing rules live in
[`RULES_AND_AGREEMENTS.md`](./RULES_AND_AGREEMENTS.md); the wire contract in
[`INTER_GROUP_TREATY_SPEC.md`](./INTER_GROUP_TREATY_SPEC.md).

### 10.1 Run topology (collapses 4 processes → 2)
```
Terminal 1 — `uv run python -m cop_thief.app`   (ONE asyncio process)
   ├─ Cop MCP server      :8001   (public, tunneled)
   ├─ Thief MCP server    :8002   (public, tunneled)
   ├─ UI SSE server       :8800   (localhost — serves grid + /stream)
   └─ Match Orchestrator  (drives matches, pushes every turn to the in-process broadcast bus)
Terminal 2 — `uv run python -m cop_thief.infra.network.switchboard`  (cloudflared tunnels → 8001/8002)
```
Because the orchestrator and the UI share **one process**, `broadcast._QUEUE` is shared and the
browser renders live moves. Localhost is needed only for the UI; the game runs in-process.

### 10.2 Decentralized model (no referee)
- Each side keeps its **own** authoritative `DecPomdpGameState`. The acting agent emits an NL move
  (`[INTENT: MOVE/BARRIER/HOLD]` + direction word); **both** sides parse it deterministically and
  apply it, so boards stay in lock-step. Thief moves first.
- A **game = 3 matches**; each side fields a **3-agent roster of strategy variants** (`AgentRoster`:
  cop_a/b/c, thief_a/b/c). Match *i* = our agent *i* vs their agent *i*.
- End-of-series: SHA-256 over the agreed `sub_games`; both groups email identical reports; mismatch →
  both score 0 (the agreement deterrent). Full transmission log is the dispute evidence.

### 10.3 Components to add
| Component | Module | Role |
|-----------|--------|------|
| App entrypoint | `cop_thief/app.py` | one event loop: MCP servers + UI + orchestrator |
| Match Orchestrator | `orchestrator/match.py` | real turn loop (thief-first), deterministic NL apply, live broadcast + audit log |
| Agent roster | `domain/strategy/roster.py` | 3 strategy variants per role |
| Defender mode | MCP tool `request_move(observation_prose) -> move_prose` | answer an incoming challenger over our URL |
| Challenger mode | MCP `Client` → opponent tunnel URLs | initiate a series against another team |

### 10.4 Phasing
- **Phase A (local, no tunnels):** Match Orchestrator runs a real Cop-vs-Thief match across the two
  local MCP servers, 3-match game, thief-first, streaming live to the UI + `game_audit.jsonl`. This
  is the strategy-iteration loop.
- **Phase B (inter-group):** swap one side's transport to the opponent's tunnel URL; add
  defender/challenger handshake; finish with SHA-256 reconcile + Gmail report + dispute logs.

*End of PLAN — approve before proceeding to TODO.md.*
