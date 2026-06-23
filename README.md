# Dual AI Agent Pursuit via MCP Servers — Dec-POMDP Cop &amp; Thief

Two autonomous AI agents — a **Cop** and a **Thief** — play a pursuit game on a
grid, **communicating only in free natural language** routed through **two
independent FastMCP servers**. The graded skill is *orchestration*: the quality
of the coordination and the robustness of the pipeline, not who wins.

> Course: *Orchestration of AI Agents*, University of Haifa (Exercise 06).
> Full spec in [`docs/PRD.md`](docs/PRD.md), architecture in [`docs/PLAN.md`](docs/PLAN.md),
> task breakdown in [`docs/TODO.md`](docs/TODO.md).

---

## 1. The formal model (Dec-POMDP)

The pursuit is a **Decentralized Partially Observable Markov Decision Process**
`⟨ n, S, {Aᵢ}, P, R, {Ωᵢ}, O, γ ⟩`:

| Symbol | Meaning here |
|--------|--------------|
| `n` | 2 agents — Cop, Thief |
| `S` | board state: cop cell, thief cell, barrier cells, barriers left, move count |
| `Aᵢ` | 8 directions + STAY; the Cop may also place a barrier |
| `P` | deterministic copy-on-write transition (illegal moves clamped) |
| `R` | scoring matrix — Cop-win 20/5, Thief-win 5/10 |
| `Ωᵢ` | the **natural-language message** each agent receives |
| `O` | maps true state → the partial, free-text observation an agent perceives |
| `γ` | RL discount (0.9, config) |

**Non-negotiable:** agents never exchange coordinates — only free text. Each side
parses the opponent's prose into an actionable belief with its own LLM (or the
offline heuristic).

---

## 2. Quickstart

```bash
uv sync                 # create the env + install everything
uv run cop-thief        # play a full game, print the JSON report
uv run pytest --cov     # 122 tests, coverage gate 90%
uv run ruff check .     # 0 lint violations
```

### Watch it play
```bash
uv run cop-thief-gui    # desktop window (Tkinter)
uv run cop-thief-web    # browser live view at http://127.0.0.1:8080
```

### The core — two MCP servers talking over the network
```bash
uv run cop-server   --port 8001          # terminal 1
uv run thief-server --port 8002          # terminal 2
uv run cop-thief-match \
  --cop-url http://127.0.0.1:8001/mcp/ \
  --thief-url http://127.0.0.1:8002/mcp/ # terminal 3 — drives a full game
```
Add `MCP_TOKEN=…` on the servers and `--cop-token/--thief-token` on the match for
bearer auth (calls without it get `401`). See [`docs/DEPLOY.md`](docs/DEPLOY.md).

### Train the adaptive (Q-Learning) pursuer
```bash
uv run cop-thief-train --episodes 20000 --out results/qtable.json
```

---

## 3. Architecture

Strictly layered; every consumer (CLI, servers, GUI, web, tests) imports **only**
the SDK — no business logic leaks out (the `CopThiefSDK` single entrypoint).

```
CLI / MCP servers / GUI / Web ──▶ CopThiefSDK ──▶ Domain ──▶ Infrastructure
                                                   │            (gatekeeper, LLM,
   Domain: grid · state machine (P) · rules        │             Gmail, logging)
           scoring · strategies · NL protocol
           agents · orchestrator · reporting
```

- **API Gatekeeper** — the single chokepoint for every external call (LLM, Gmail):
  per-service rate limits (config), retry-with-backoff, structured logging, and a
  controlled `BackpressureError` that never crashes. ([`PRD_gatekeeper`](docs/PRD_gatekeeper.md))
- **Natural-language protocol** — encoder (state → prose), parser (prose →
  `BeliefUpdate`, LLM via gatekeeper with an offline heuristic fallback), and a
  belief-driven strategy. ([`PRD_nl_protocol`](docs/PRD_nl_protocol.md))
- **Strategies** — heuristic (Chebyshev pursuit/evasion, full obs), belief-aware
  (faithful partial obs), and tabular **Q-Learning**. ([`PRD_rl_qtable`](docs/PRD_rl_qtable.md))
- **Gmail reporter** — OAuth2 desktop flow, **JSON-only** body, single send, via
  the gatekeeper. ([`PRD_gmail_oauth`](docs/PRD_gmail_oauth.md))
- **Token budget** — estimate/accumulate LLM token usage &amp; cost. ([`PRD_token_budget`](docs/PRD_token_budget.md))

---

## 4. Configuration (no hardcoding)

All gameplay/infra parameters live in versioned JSON:

| File | Holds |
|------|-------|
| [`config/setup.json`](config/setup.json) | grid size, max moves, num games, max barriers, scoring, seed |
| [`config/rate_limits.json`](config/rate_limits.json) | per-service gatekeeper limits |
| [`config/rl.json`](config/rl.json) | Q-Learning α, γ, ε schedule, rewards |

The **sanity progression** is config-only — no code change between board sizes:
```bash
uv run cop-thief --config config/setup_2x2.json
uv run cop-thief --config config/setup_3x3.json
```

---

## 5. The bonus — inter-group competition

A bilateral cloud series of 6 sub-games with **role-swapping** (Group A's Cop vs
B's Thief, then swapped). Each group emails its **own** report; both must match
(`mutual_agreement: true`) or the series scores 0/0. Scoring 10 / 7 / 5, averaged
over series. The machinery (`BonusSeriesController`, `BonusReport`,
`AgreementReconciler`) and the **tool contract both groups must implement** are in
[`docs/BONUS.md`](docs/BONUS.md).

---

## 6. Quality gates

| Gate | Status |
|------|--------|
| Package manager | `uv` only |
| File size | ≤ 150 LOC per file |
| SDK boundary | enforced (architecture test) |
| Gatekeeper | all external calls routed through it |
| No hardcoding | params in versioned JSON |
| Test coverage | **≥ 90%** (`pytest --cov`) |
| Linting | `ruff check` = 0 |
| Secrets | `.env` only; `credentials.json`/`token.json` git-ignored |

---

## 7. Commands

| Command | What it does |
|---------|--------------|
| `cop-thief` | Play a full game; print the internal JSON report |
| `cop-thief-gui` | Tkinter desktop visualization |
| `cop-thief-web` | Browser SSE live view (`:8080`) |
| `cop-thief-train` | Train + save the Q-Learning table |
| `cop-server` / `thief-server` | Launch an MCP agent server |
| `cop-thief-match` | Drive a full game across two MCP servers |

---

## 8. Layout

```
src/cop_thief/
  config/        versioned config models + loaders
  domain/        grid, state machine, rules, scoring, strategy, nl, agents, reporting
  orchestrator/  local loop, bonus series, MCP client, remote game
  infra/         gatekeeper, rate limiter, retry, llm client, token tracker, logger
  servers/       FastMCP Cop/Thief servers + token auth
  auth/          OAuth2 flow + Gmail reporter
  gui/           Tkinter app
  ui/            Starlette + SSE web app
tests/           unit + integration (~98% coverage)
docs/            PRD, PLAN, TODO, BONUS, DEPLOY + 5 companion PRDs
```

## 9. Documentation

- [`PRD.md`](docs/PRD.md) · [`PLAN.md`](docs/PLAN.md) · [`TODO.md`](docs/TODO.md)
- Companion PRDs: [gatekeeper](docs/PRD_gatekeeper.md) · [NL protocol](docs/PRD_nl_protocol.md)
  · [Q-Learning](docs/PRD_rl_qtable.md) · [Gmail/OAuth](docs/PRD_gmail_oauth.md)
  · [token budget](docs/PRD_token_budget.md)
- [`BONUS.md`](docs/BONUS.md) — inter-group contract · [`DEPLOY.md`](docs/DEPLOY.md) — cloud + auth

## 10. Credits

University of Haifa — *Orchestration of AI Agents* (Dr. Yoram Segal), Exercise 06.
