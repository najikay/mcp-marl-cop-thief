# PRD — Product Requirements Document
## Dual AI Agent Conversation via MCP Servers — Dec-POMDP Cop & Thief Chase

| Field | Value |
|-------|-------|
| Project | `marl-cop-thief` — Orchestration of two autonomous AI agents over MCP |
| Assignment | Exercise 06 (HW6), Course "Orchestration of AI Agents", University of Haifa |
| Author of brief | Dr. Yoram Segal |
| Document version | 1.00 |
| Status | Draft — must be approved before any code is written (mandatory workflow, Guidelines §2.5) |
| Companion docs | [`PLAN.md`](./PLAN.md), [`TODO.md`](./TODO.md), per-mechanism PRDs (see §10) |

> **Governing standard.** This project is graded against Dr. Segal's *"Guidelines for Writing
> Professional Software at the Highest Level of Excellence" (v3.00)*. Every requirement below is
> written so that it is **measurable, testable, and traceable** to a task in `TODO.md`.

---

## 1. Executive Summary & Problem Statement

### 1.1 Executive Summary
We are building a **full end-to-end pipeline** that allows two autonomous AI agents — **the Cop**
(`Cop`) and **the Thief** (`Thief`) — to play a pursuit game on a 2-D grid, **communicating with
each other exclusively in free natural language** routed through **two independent FastMCP
servers**. The central deliverable is **orchestration**, not the game outcome and not the strategy:
the grade is earned by the *quality of the conversation and coordination* between the two agents,
the robustness of the pipeline, and adherence to the engineering excellence standard.

The system must run first **locally** (two servers on `localhost`, separate ports), then be promoted
**to the cloud** (public MCP URLs protected by tokens), and optionally enter a **bonus inter-group
competition**. At the end of every full game, the Cop agent autonomously emails a **structured
JSON report** to the examiner via the **Gmail API**, and both agents must reach **mutual agreement**
on that report.

### 1.2 Problem Statement
Two agents must make **autonomous, real-time decisions under partial observability** while sitting
on opposite sides of a network boundary. Neither agent has full visibility of the world; each must
**infer the opponent's position from natural-language messages**, translate those inferences into
grid actions, and converge on a shared, verifiable record of what happened. The engineering problem
is therefore *distributed multi-agent coordination*, layered on top of strict professional-software
constraints (modularity, an SDK boundary, a centralized API gatekeeper, configuration-driven
behavior, TDD with ≥85 % coverage, and zero linter violations).

### 1.3 Formal Model — The Dec-POMDP Tuple
The pursuit is formalized as a **Decentralized Partially Observable Markov Decision Process**:

```
Dec-POMDP = ⟨ n, S, {A_i}, P, R, {Ω_i}, O, γ ⟩
```

| Symbol | Name | Meaning in this project |
|--------|------|--------------------------|
| `n` | Number of agents | `n = 2` (Cop, Thief). |
| `S` | State space | Full board state: cop coordinates, thief coordinates, set of placed barrier cells, barriers-remaining counter, move counter. For an `R×C` grid the joint position space is bounded by `(R·C)²`. |
| `A_i` | Action set of agent *i* | Cop: move in 8 directions (incl. diagonal) **or** place a barrier on its current cell. Thief: move in 8 directions. "Stay" is a degenerate move. |
| `P` | Transition function | `P(s' \| s, a_cop, a_thief)` — deterministic board update from the joint action; the board is a **state machine** where each step yields a new state. Illegal moves (into a wall, edge, or barrier) are rejected/clamped. |
| `R` | Reward / scoring | Capture & evasion scoring (see §3.4). Used both as the official score and as the RL reward signal. |
| `Ω_i` | Observation space of agent *i* | The partial, natural-language description each agent receives (its own position, its noisy belief about the opponent, hints/deception in messages). |
| `O` | Observation function | `O(o_i \| s', a)` — maps the true next state to the partial observation each agent actually perceives (partial observability: an agent does not directly read the opponent's coordinates). |
| `γ` | Discount factor | RL discount, default `0.9` (config-driven; see [`PRD_rl_qtable.md`](./PRD_rl_qtable.md)). |

> **Key constraint (non-negotiable).** Agents **do not** exchange numeric coordinates over a rigid
> protocol. They exchange **free natural-language messages**; the receiving agent uses its LLM to
> *parse* unstructured text into actionable grid vectors and inferred barriers. The internal
> implementation of each agent is private and may differ between groups.

---

## 2. Target Audience & System Personas

| Persona | Type | Goals | What success looks like |
|---------|------|-------|--------------------------|
| **The Cop** | Autonomous AI agent | Capture the Thief (land on the same cell) within `max_moves`; spend up to `max_barriers` barriers strategically; avoid draws. At end-of-game, emit the JSON report via Gmail API. | Captures often, places barriers wisely, communicates and reports correctly. |
| **The Thief** | Autonomous AI agent | Survive `max_moves` per sub-game without being caught; exploit partial observability and deception; avoid draws. | Evades reliably; agrees with the Cop on the final report. |
| **The Orchestrator** | System role (MCP Client / game engine) | Drive the turn loop, route natural-language messages between the two MCP servers, query the LLM for decisions, enforce rules, persist logs, trigger reporting. *(This is the component the students actually build and own.)* | Game completes deterministically; logs are dispute-proof; reports are generated. |
| **The Examiner** | Human grader (Dr. Segal / TA) | Receive a single, **JSON-only** result email at `rmisegal+uoh26b@gmail.com`; verify mutual agreement; inspect the GitHub repo, README scientific analysis, logs, and run the sanity progression. | Email parses automatically; reports from both sides match; repo passes the quality gate. |

Secondary audiences: **rival groups** (bonus matchmaking partners) and **future maintainers**
(extension points & docs).

---

## 3. Measurable KPIs & Acceptance Criteria

### 3.1 Product / Game KPIs
| # | KPI | Target | Verification |
|---|-----|--------|--------------|
| K1 | Natural-language only protocol | 100 % of inter-agent turns are free-text; **zero** rigid numeric-coordinate messages on the wire | Message-log audit / integration test |
| K2 | Full game completes | A "Game" = exactly **6 valid sub-games**, each ≤ `max_moves` moves | End-to-end run |
| K3 | **Mutual agreement (non-negotiable)** | Both agents independently produce **byte-identical game outcome** in their JSON reports (`mutual_agreement = true`) | Diff of the two reports |
| K4 | Technical-loss handling | Any sub-game aborted by a technical failure is marked void and **re-run** until 6 valid sub-games exist | Fault-injection test |
| K5 | Draw avoidance | Strategy explicitly avoids draws (deterministic tie-break / capture-seeking) | Strategy test on adversarial fixtures |
| K6 | Report delivery | Exactly **one** email, **JSON body only** (no free text), to the examiner address, via Gmail API | Mail-send integration test (mocked + one real dry-run) |
| K7 | Scoring correctness | Per-sub-game and totals match the scoring table exactly; scoring values are **immutable** and config-sourced | Unit tests over the scoring matrix |
| K8 (**UI-01**) | Real-time observability GUI | Native zero-dependency `tkinter` window renders the live grid + scrolling NL banter feed without blocking the game loop | Visual unit test + manual run |
| K9 (**SEC-03**) | Burner sandbox dry-run | Final JSON handshake is first sent **burner→burner** (`mcp.marl.telemetry@gmail.com` self-loop) and verified before the live Examiner address is ever contacted | Loopback dry-run integration test |
| K10 (**CLOUD-02**) | Persistent public HTTPS endpoints | Two revocable-token-secured HTTPS URLs (Cloudflare Tunnel / Localtonet) front the local FastMCP servers | Security assertion tests (token required; HTTPS reachable) |

> **Acceptance gate K3 is non-negotiable:** if the two agents' end-game JSON reports do **not** agree,
> the deliverable fails this criterion (and, in the bonus, both groups score **0** for that series).

### 3.2 Sanity Testing Progression (4 stages, **must** pass in order)
Per the assignment, do **not** start at 5×5. Integration is proven by climbing grid sizes:

| Stage | Grid | Objective | Complexity |
|-------|------|-----------|------------|
| **1** | **2×2** | Algorithmic sanity; basic integration; verify the message **pipeline** end-to-end | Very low |
| **2** | **3×3** (or 3×2) | Convergence of the coordination mechanism; hyper-parameter tuning; failure detection | Medium |
| **3** | **4×4** (or 4×3) | Stress **partial observability**: starting distance exceeds the vision radius | High |
| **4** | **5×5** | Final exam run; produce graphs; full-game outcome analysis | Maximum |

**Acceptance:** each stage must complete a full 6-sub-game game with valid reports before the next
grid size is enabled (grid size is config-driven; no code change between stages).

### 3.3 Engineering KPIs (from Guidelines v3.00 — hard gates)
| # | Gate | Threshold | Enforcement |
|---|------|-----------|-------------|
| E1 | Package manager | `uv` only — **zero** `pip` / `virtualenv` / `python -m` calls anywhere | grep audit + CI |
| E2 | File size | ≤ **150** code lines per file | line-count check |
| E3 | SDK boundary | 100 % of business logic reachable only via the SDK single entrypoint | code review |
| E4 | API Gatekeeper | 100 % of external calls (LLM + Gmail) routed through the gatekeeper; FIFO queue; **never crashes on overflow** | code review + backpressure test |
| E5 | DRY / OOP | Zero duplicated logic; base classes / single-concern mixins / template methods | review + duplication scan |
| E6 | No hardcoding | 100 % of grid sizes, timeouts, scoring, rate limits in versioned JSON/YAML | hardcode scan (Table 1, Guidelines §7.2) |
| E7 | Test coverage | ≥ **85 %** (`pytest --cov`); build fails under threshold | `pyproject.toml` `fail_under = 85` |
| E8 | Linting | **0** `ruff check` violations | CI |
| E9 | Versioning | Code + every config file carry an explicit version starting at `1.00` | startup validation |
| E10 | Secrets | No API keys/tokens in source; `.env`-only; `.env-example` committed; `credentials.json` git-ignored | secret scan |

### 3.4 Scoring Matrix (immutable — values may **not** change)
Per single sub-game (config keys in parentheses):

| Sub-game outcome | Cop score | Thief score |
|------------------|-----------|-------------|
| **Cop wins** (capture) | **20** (`scoring.cop_win`) | **5** (`scoring.thief_loss`) |
| **Thief wins** (evades `max_moves`) | **5** (`scoring.cop_loss`) | **10** (`scoring.thief_win`) |

- **Win — Cop:** the Cop arrives on the exact cell occupied by the Thief.
- **Win — Thief:** the Thief survives `max_moves` (default 25) without the Cop landing on its cell.
- **Barrier:** as an alternative to moving, the Cop may place a barrier on its **current** cell;
  that cell becomes an impassable wall for **both** agents thereafter. Cop ≤ `max_barriers`
  (default 5) per sub-game; the Thief may **never** place barriers.
- **Per full game (6 sub-games):** max attainable per group = **90** (`3×20` as Cop + `3×10` as
  Thief); min = **30**.

### 3.5 Bonus — Inter-Group Competition (optional, up to +10 project points)
- A bonus match is a full bilateral cloud game between **two groups**: a series of 6 sub-games.
  First 3 sub-games: Group A's Cop vs Group B's Thief; last 3: Group B's Cop vs Group A's Thief.
- Each group **independently** emails a separate report with the **exact same** result
  (`mutual_agreement = true`).
- Per series: highest cumulative score → **10**; losing group → **7**; absolute tie → **5** each.
- Final bonus = **average** over all valid series (e.g. won one of two series → `(10+7)/2 = 8.5`).
- **Mismatch or disagreement between the two reports → series cancelled → 0 points for both sides.**
- Playing more than one group is allowed and encouraged.
- Bonus submission deadline: by **Friday 08:30** before the lecture, within one week of publication.
  Submitting the bonus also grants an extension on HW5 (to **2026-07-03**).

---

## 4. Functional & Non-Functional Requirements

### 4.1 Functional Requirements
| ID | Requirement |
|----|-------------|
| F-01 | Model a configurable `R×C` grid (default 5×5) as a state machine; one state mutation per step. |
| F-02 | Random (or strategically chosen) start positions for Cop and Thief; 8-directional movement incl. diagonals; clamped/rejected illegal moves. |
| F-03 | Barrier placement by the Cop (≤ `max_barriers`); barrier cell becomes impassable for both agents. |
| F-04 | Turn arbiter: one move at a time, turn-based (Thief typically first), alternating until terminal. |
| F-05 | Capture and evasion detection; sub-game termination at capture or at `max_moves`. |
| F-06 | Sub-game ≤ `max_moves` (25); Game = `num_games` (6) consecutive sub-games with accumulated totals. |
| F-07 | Two FastMCP servers (Cop server, Thief server), each exposing tools for: send message, receive message, propose move, mutual-agreement verification. |
| F-08 | Orchestrator (MCP Client) drives the loop, routes **natural-language** messages, queries the LLM for tool decisions, and aggregates results. |
| F-09 | LLM-based natural-language parser: convert unstructured opponent text into grid vectors / inferred barriers (the agent's belief update). |
| F-10 | Strategy/decision module (heuristic / Manhattan-distance / tabular **Q-Learning**); must avoid draws. |
| F-11 | Centralized **API Gatekeeper** wrapping all LLM and Gmail calls: FIFO queue, config-driven rate limiting, retries, monitoring, graceful overflow. |
| F-12 | Configuration manager loading versioned JSON/YAML; no hardcoded parameters. |
| F-13 | Structured logging of every move, message, and decision (dispute-proof audit trail). |
| F-14 | End-of-game JSON report generation (internal schema) + bonus inter-group schema. |
| F-15 | **Cop** auto-triggers Gmail-API send of the **JSON-only** report at end of game. |
| F-16 | Mutual-agreement reconciliation: both agents converge on identical outcome before sending. |
| F-17 | GUI (optional but in scope) visualizing real-time agent/barrier movement and (bonus) the Q-Table. |
| F-18 | CLI entrypoint to run a game at a given grid size, all via `uv run`. |
| **UI-01** | **Native `tkinter` real-time observer GUI** — zero extra dependencies. Left pane: a 5×5 (config-driven) `Canvas` updating agent coordinates each tick — **Blue = Cop, Red = Thief, Black = active Barriers**. Right pane: a scrolling text feed live-streaming the natural-language prose banter between the agents. The GUI consumes updates via a **thread-safe queue** and never blocks the game loop. |
| **SEC-03** | **Sandbox Loopback Guard** — the Gmail Reporter supports a *"Burner Sandbox Dry-Run"* mode that sends the final JSON handshake from `mcp.marl.telemetry@gmail.com` **to itself** (`mcp.marl.telemetry@gmail.com`) to validate Gmail-API formatting/auth. The live Examiner address (`rmisegal+uoh26b@gmail.com`) is contacted **only** after a successful burner loopback (enforced by a `SubmissionSafetyGuard` interlock). |
| **CLOUD-02** | **Persistent public HTTPS endpoints** — provision two durable public HTTPS URLs via **Cloudflare Tunnels (`cloudflared`)** or **Localtonet**, fronting the local FastMCP instances and secured by **revocable bearer tokens** (one Cop URL, one Thief URL). |
| **MATCH-01** | **Decentralized match play (no referee).** The two agents decide the game together: each side keeps its own authoritative board and applies the peer's NL moves; **disagreement on the result → both groups score 0** (see [`RULES_AND_AGREEMENTS.md`](./RULES_AND_AGREEMENTS.md)). |
| **MATCH-02** | **Defender / Challenger duality.** Each server can (a) **accept** an incoming challenge (`request_move` tool) or (b) **initiate** a challenge against another team's URLs. Thief always moves first. |
| **MATCH-03** | **Game = 3 matches; 3-agent roster.** Each side fields **3 strategy-variant agents** per role; match *i* = our agent *i* vs their agent *i*. |
| **MATCH-04** | **Live observability (mandatory for strategy work).** Every match renders on the UI (moving Cop/Thief/Barriers) **and** is appended to `data/game_audit.jsonl` in real time — the orchestrator and UI run in one process so the broadcast bus is shared. |
| **MATCH-05** | **Single-app topology.** One process hosts both MCP servers + the UI + the match orchestrator; a second process runs the Cloudflare tunnels. (Two terminals, not four.) |
| **MATCH-06** | **Dispute evidence.** Per-turn transmissions, board hashes, and the SHA-256 series hash are retained as the evidence record for lecturer adjudication on suspected cheating. |
| **SEC-04** | **Injection resilience.** Inbound opponent transmissions are screened for prompt-injection / coercion signatures (e.g. "ignore previous instructions", "concede", "submit a loss", "this is a test", threats). Our move is always self-computed and there is **no forfeit action**, so no transmission can make our agent throw the game; hostile transmissions are logged (`hostile: true`) and counted as evidence. |
| **NET-05** | **Real cross-host transport.** Moves are fetched by an MCP `Client` calling the partner's `request_move` tool over its `/sse` endpoint (per-role bearer token). The same `RemoteMoveClient` targets our own local `/sse` endpoints in mirror mode, so the live game runs over real MCP-over-SSE sockets — identical to playing a partner's tunnel URL. |
| **REC-01** | **Mutual-agreement reconciliation.** After the 6 sub-games both sides hash the canonical `sub_games` array; equal digests ⇒ `mutual_agreement: true` (totals stand), any mismatch ⇒ `mutual_agreement: false` and a 0/0 `both_lose` scoreline. |
| **STRAT-01** | **Barrier mechanic (ex06 §4.3).** As an alternative to moving, the Cop may wall **its own current cell** (`[INTENT: BARRIER]`); the cell becomes impassable to both, budget ≤ 5/sub-game, Thief never. The *mechanic* is implemented and validated; *when* to spend a wall (multi-step herding toward `thief_trapped`) is owned by the strategy layer, not auto-emitted by the geometry resolver. |
| **STRAT-02** | **Game-theoretic minimax (Markov game).** Each `request_move` is answered by depth-limited **alpha-beta** over the zero-sum game (Cop max, Thief min, optimal-adversary assumption). Progress-shaped terminal scores (`±WIN ∓ turns`) make the policy press for capture/survival, so **draws are structurally avoided**. Three variant profiles (aggressive/balanced/defensive) drive the 6 sub-games. See [`STRATEGY.md`](./STRATEGY.md). |
| **STRAT-03** | **Conway Angel–Devil barriers.** The Cop's search action set includes walling its own cell (§4.3); the evaluation's *containment* term is the Thief's flood-filled escape region, so the planner discovers legal herding-to-trap lines (no hand-coded barrier rule). |
| **STRAT-04** | **Advanced RL (self-play).** The linear evaluation weights are learned by **self-play TD** with a minimax backup (function approximation, ε-exploration) — beyond the assignment's tabular Q. `train_weights()` returns the learned vector; live play uses tuned defaults. |
| **STRAT-05** | **Adapt to a sub-optimal opponent.** A **pessimism knob** interpolates minimax↔expectimax; an online `OpponentModel` estimates the opponent's rational-rate from observed moves and lowers pessimism only as far as proven exploitable (maximin vs best-response). Variants differ by `risk` (aggressive exploits, defensive stays pure-minimax). |
| **GAME-02** | **Random openings (§4.2).** Each sub-game starts from a seeded-random, distinct Cop/Thief placement (`game.start_mode`/`random_seed`); the seed is deterministic so both groups reproduce the same opening (no agreement drift). |
| **NET-06** | **Interactive cross-host challenge.** `python -m cop_thief.challenge` prompts for our/opponent group names, the opponent's COP/THIEF MCP URLs (`…/mcp/` or `…/sse`), tokens and report email; it preflights the opponent's `request_move`, then plays 6 sub-games with **per-leg routing** (our role local, opponent's role fetched over MCP) and emails the JSON `bonus_game` report. Opponent details are runtime input, not hardcoded. |

### 4.2 Non-Functional Requirements
| ID | Category | Requirement |
|----|----------|-------------|
| N-01 | **Security — OAuth tokens over passwords** | Gmail access uses OAuth2 **Desktop-app** client with `gmail.modify` scope. **No passwords.** A stored password is exposed on breach; an OAuth token is short-lived, scoped, and revocable. `credentials.json` (downloaded & renamed from the Google Cloud OAuth client) and `token.json` are **git-ignored**; the test account is registered as a Test User. |
| N-02 | **Security — network/secrets** | MCP URLs must not be openly reachable; protect with **token authentication** that can be **revoked**. No keys in source; `.env` only. Do not run servers from a firewalled workplace network. |
| N-03 | **Public tunneling** | When exposing a local LLM/server, use **ngrok** (Traffic Policy / Basic Auth), **Localtonet**, or **Nginx** reverse proxy (SSL termination, htpasswd, Certbot, firewall). Prefer the **hybrid** model: only MCP servers in cloud, outbound-only HTTPS, Ollama stays local. |
| N-04 | **Gmail API reporting** | Reporting goes through the Gmail API (Google API Client), not raw SMTP, for reliability and to avoid mail-server failures. Body = JSON only. |
| N-05 | Reliability | Gatekeeper retries transient failures; orchestrator survives sub-game faults (re-run void sub-games). |
| N-06 | Performance / cost | Prefer cloud LLM API for stability & near-zero token cost on short messages; batch where possible; track token cost. |
| N-07 | Portability | Two public URLs per group (one Cop, one Thief) via **Cloudflare tunnels** (`switchboard.py`); transport-agnostic MCP-over-HTTP. |
| N-08 | Maintainability | Modular packages, SDK boundary, ≤150-LOC files, ISO/IEC 25010 alignment. |
| N-09 | Observability | Per-run logs (success & failure), pass/fail test reports, optional CLI/GUI live view. |
| N-10 | Networking transport | Servers communicate over **HTTP/HTTPS** (HTTP mandatory locally). |

### 4.3 Representative User Stories
- *As the Orchestrator,* I route a Thief's taunt ("you'll never reach the north-east corner before I
  slip past the wall you just built") to the Cop so the Cop's LLM can update its belief and pick a move.
- *As the Cop,* when the game ends I assemble the JSON report and send it via Gmail API without any
  human action.
- *As the Examiner,* I receive one JSON-only email per group and confirm both groups' reports match.
- *As a Developer,* I change `grid_size` in config from `[2,2]` to `[5,5]` and re-run with **no code change**.

---

## 5. Constraints, Assumptions & Dependencies
- **Constraints:** `uv`-only; ≤150 LOC/file; SDK boundary; gatekeeper for all external calls;
  natural-language-only game protocol; config-driven everything; scoring values immutable.
- **Assumptions:** each group operates two reachable MCP endpoints; a Gmail test account exists and
  is registered as an OAuth Test User; an LLM is available (cloud API key **or** local Ollama).
- **Dependencies:** FastMCP; an LLM provider (cloud API or Ollama); Google API Client (Gmail);
  a tunneling/cloud platform; `pytest`/`pytest-cov`; `ruff`.

---

## 6. Out-of-Scope Boundaries
The following are **explicitly out of scope** for this deliverable:
1. Deep neural-network RL (DQN/PPO/actor-critic). RL is **optional**; if used, **tabular Q-Learning** only.
2. A rigid, machine-parseable game wire-protocol between agents — **forbidden**; only natural language.
3. Cross-group rule enforcement — inter-group agreements are allowed but **not enforceable**.
4. Changing the **scoring point values** — fixed by the brief.
5. Production-grade multi-tenant hosting / horizontal autoscaling beyond the two required URLs.
6. Human-in-the-loop play — agents are **fully autonomous** from sub-game start to report send.
7. Calendar features of the Google API (the `calendar` scope is set up per the guide but unused here).
8. Persisting personal secrets in the repository (only `.env-example` placeholders are committed).

---

## 7. Risks & Mitigations
| Risk | Impact | Mitigation |
|------|--------|------------|
| Reports disagree (K3 fails) | Lose points / 0 in bonus | Deterministic state machine + explicit reconciliation tool + shared log hash |
| LLM misparses natural language → illegal move | Stalled/void sub-game | Validation + graceful fallback + technical-loss re-run |
| External rate limits / outages | Pipeline crash | Gatekeeper FIFO queue, backpressure, retries — never crash on overflow |
| Secret leakage | Security breach | OAuth tokens, `.env`, git-ignore, revoke capability |
| Files exceed 150 LOC | Quality-gate failure | Aggressive modularization (mixins, helper modules, constants split) |

---

## 8. Release Milestones (summary; detail in `PLAN.md` / `TODO.md`)

> **Status (v2.0):** M1–M7 are **implemented and verified** (109 tests / ~95 % coverage / `ruff` clean /
> files ≤150 LOC); all §4.1 functional requirements (incl. MATCH-01…06, SEC-04, NET-05/06, REC-01,
> STRAT-01…05, GAME-02) are met. M8 sanity progression is **supported by config** (5×5 validated; 2×2→4×4
> not run as separate suites). M9 uses **Cloudflare tunnels** (not Prefect Cloud). Remaining pre-game
> cycles: README+screenshots, active injection counter-measure, dispute log archive, §9.2 schema
> convergence, and the live inter-group run — see `TODO.md` → Milestone 6 / AS-BUILT RECONCILIATION.

1. **M1 — Core domain & state machine** (Phase 1).
2. **M2 — Enterprise infra: config, versioning, uv, ruff** (Phase 2).
3. **M3 — API Gatekeeper & rate limiting** (Phase 3).
4. **M4 — SDK layer** (Phase 4).
5. **M5 — Cop & Thief FastMCP servers** (Phases 5–6).
6. **M6 — Orchestrator + NL parser** (Phase 7).
7. **M7 — OAuth2 desktop client + Gmail JSON reporter** (Phase 8), including the **SEC-03 Sandbox Loopback Guard** (`SubmissionSafetyGuard`, Phase 8.E) and the **UI-01 native `tkinter` observer GUI** (Phase 8.F).
8. **M8 — Sanity progression 2×2 → 5×5** (Phase 9), culminating in the **SEC-03 Burner Loopback Dry-Run** (Phase 9.E).
9. **M9 — Cloud tunneling + bonus matchmaking prep** (Phase 10): provision the **CLOUD-02** persistent public HTTPS tunnels (Cloudflare/Localtonet) with revocable-token security assertions (Phase 10.A).

---

## 9. Acceptance Definition of Done (project-level)
The project is **done** when: all 10 engineering gates (E1–E10) pass; the 4-stage sanity progression
completes; a full 6-sub-game game produces **mutually-agreed** JSON reports; the Cop emails the
JSON-only report via Gmail API; `README.md` contains the formal Dec-POMDP model and scientific
analysis; and `PRD.md`, `PLAN.md`, `TODO.md` (+ per-mechanism PRDs) are approved.

## 10. Companion Per-Mechanism PRDs (Guidelines §2.3 — mandatory for each central mechanism)
- [`PRD_rl_qtable.md`](./PRD_rl_qtable.md) — Tabular Q-Learning strategy (Bellman update, ε-greedy, reward shaping, 3-tier stack).
- [`PRD_nl_protocol.md`](./PRD_nl_protocol.md) — Natural-language Dec-POMDP message protocol, defensive parser & Diplomat negotiation.
- [`PRD_gatekeeper.md`](./PRD_gatekeeper.md) — API Gatekeeper (FIFO, rate limit, retry, backpressure, token-interception).
- [`PRD_gmail_oauth.md`](./PRD_gmail_oauth.md) — OAuth2 Desktop client & Gmail JSON reporter, K3 agreement hashing.
- [`PRD_token_budget.md`](./PRD_token_budget.md) — **Token economics, real-time telemetry & budget tracker** (architecture expansion).

*End of PRD — approve before proceeding to PLAN.md.*
