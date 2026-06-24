# MARL Cop & Thief — Dual AI Agents over MCP

A decentralized, partially-observable **pursuit game** between two autonomous AI agents — the **Cop**
and the **Thief** — that converse in **free natural language** over **MCP** servers, decide moves with
a **game-theoretic minimax + self-play RL** engine, render live in a **web control panel**, and email a
mutually-agreed **JSON match report** via the Gmail API.

> University of Haifa · *Orchestration of AI Agents* (ex06) · Dr. Yoram Segal.
> One command launches everything; one browser tab runs a whole match.

---

## Highlights

- **One-command node** — `python -m cop_thief.app` boots both MCP servers, the public Cloudflare
  tunnels, **and** a browser control panel together (no orphan tunnels, no port juggling).
- **Web control panel** — live node status, copy-ready public URLs/tokens, an opponent **challenge
  form**, a one-click **mirror self-test**, and a live 5×5 game TV — all at `http://127.0.0.1:8800`.
- **Real strategy** — an **Angel–Devil minimax** engine (zero-sum Markov game, alpha-beta) with the
  **Conway** blocking game (Cop = Devil walls §4.3) and **self-play RL** weight learning, well beyond
  the assignment's baseline tabular Q. See [`docs/STRATEGY.md`](docs/STRATEGY.md).
- **Decentralized & cheat-resistant** — no referee; both sides hash the result (SHA-256) and **any
  disagreement scores 0/0**. Inbound prose is treated as hostile: prompt-injection / coercion is
  **screened, logged as evidence, and cannot change the outcome** (no forfeit action exists).
- **Single SDK boundary + API Gatekeeper** — all logic behind `CopThiefSDK`; every external call (LLM,
  Gmail) funneled through a FIFO-backpressured gatekeeper with DeepSeek→Anthropic failover.
- **Quality gates** — `pytest` ≥ 85 % coverage, zero-violation `ruff`, ≤ 150 lines/file, uv-only.

---

## Quick start

```bash
uv sync                                   # install (uv is the ONLY package manager)
cp .env-example .env                      # fill in real values (see "Secrets")
uv run ruff check .                       # zero-violation lint gate
uv run pytest                             # full suite (>=85% coverage gate)
uv run python -m cop_thief.app            # launch the control panel + servers + tunnels
```

Then open **`http://127.0.0.1:8800`**.

---

## Playing a match (control panel)

1. `uv run python -m cop_thief.app` → the panel opens; wait for **Servers ●** and **Tunnels ●** green.
2. The status card shows your two public `…/mcp/` URLs + per-role tokens (copy buttons). **Send these to
   your opponent** along with [`docs/INTER_GROUP_TREATY_SPEC.md`](docs/INTER_GROUP_TREATY_SPEC.md).
3. Paste the opponent's two `…/mcp/` URLs (and tokens, if any) into the **challenge form**, then
   **START CHALLENGE** — the 6 sub-games play cross-host on the TV and the report is emailed.
4. No partner yet? Click **MIRROR SELF-TEST ⟳** — it fills your own localhost endpoints + tokens and
   plays you against yourself (ideal for strategy testing).

A **game = 6 sub-games** (per §4.1): we play **Cop in 3** (home leg) and **Thief in 3** (away leg),
Thief-first, ≤ 25 moves each. Scoring is immutable: Cop capture → **20 / 5**; Thief survives → **5 / 10**.

---

## Architecture

| Layer | Module | Responsibility |
|---|---|---|
| Domain | `domain/` | Immutable `DecPomdpGameState`, `Grid`, geometry, NL move language (`[INTENT: …]`). |
| Strategy | `domain/strategy/` | `minimax` (alpha-beta), `evaluation`/`features` (Angel–Devil), `selfplay` (RL), Q-table baseline. |
| SDK | `sdk/` | `CopThiefSDK` single entrypoint; `MatchCoordinator` terminal/trapped-death logic; warfare/injection screen. |
| Gatekeeper | `infra/gatekeeper/` | FIFO chokepoint for all LLM/Gmail calls; DeepSeek→Anthropic failover; token telemetry. |
| Servers | `servers/` | Cop & Thief FastMCP servers; token auth; `request_move` tool → `StrategyResolver`. |
| Transport | `infra/network/` | streamable-HTTP `/mcp` host, `RemoteMoveClient`, Cloudflare switchboard. |
| Orchestration | `orchestrator/` | `ChallengeRunner` (cross-host, per-leg), `reconcile` (mutual agreement / 0-0), series. |
| UI | `ui/` | Control-panel backend (`server.py`), `NodeState`, broadcast SSE bus, `static/panel.html`. |
| Reporting | `reporting/` | Gmail OAuth reporter (group name in subject + body), append-only audit log, safety guard. |

### Entry points
| Command | What it does |
|---|---|
| `python -m cop_thief.app` | **Control panel**: servers + tunnels + web UI (the main one). |
| `python -m cop_thief.challenge` | Interactive terminal cross-host challenge (prompts for opponent URLs). |
| `python -m cop_thief.serve` | Servers + tunnels only (no UI). |
| `python -m cop_thief.infra.network.dual_mcp_host` | Just the two MCP servers (`:8001`/`:8002` `/mcp`). |
| `python -m cop_thief.diagnostic_runner` | Offline, zero-cost pursuit probe (mocked LLM). |

---

## Strategy in one paragraph

Each `request_move` is answered by depth-limited **alpha-beta minimax** over the zero-sum Markov game
(Cop maximizes, Thief minimizes, optimal-adversary assumption). Progress-shaped terminal scores
(`±WIN ∓ turns`) make the policy press for capture/survival, so **draws are structurally avoided**. The
Cop's action set includes **walling its own cell** (Conway "Devil" move, §4.3); the evaluation's
*containment* feature is the Thief's flood-filled escape region, so the planner discovers legal
herding-to-trap lines on its own. The linear evaluation weights are tunable by **self-play TD**
(`selfplay.train_weights`). Three variant profiles (aggressive / balanced / defensive) field the
required 3-agent roster. Full design: [`docs/STRATEGY.md`](docs/STRATEGY.md).

---

## Security & fair play

- **Tokens** — every MCP tool call requires a per-role revocable bearer token; exchanged out-of-band,
  rotatable to revoke. Servers are fail-closed.
- **Anti-injection** — inbound transmissions are untrusted; injection/coercion/impersonation/forgery
  are screened, flagged `hostile:true` in `data/game_audit.jsonl`, counted in the report, and have **no
  effect on the engine-determined outcome**. Codified for opponents in the treaty (§F).
- **Mutual agreement** — both sides hash the canonical `sub_games`; **any mismatch ⇒ 0/0** (`both_lose`).
- **Reporting** — Gmail API over OAuth2 Desktop (scope `gmail.modify`, zero passwords); the group name
  rides in both the subject line and the JSON body; a safety guard defaults to the burner inbox.

---

## Secrets & configuration

- Copy `.env-example` → `.env` and fill: `DEEPSEEK_API_KEY`, `ANTHROPIC_API_KEY`, `COP_MCP_TOKEN`,
  `THIEF_MCP_TOKEN`, `GMAIL_CREDENTIALS_PATH`. A zero-dependency autoloader injects `.env` at startup —
  no `export`/`source` needed; existing shell exports always win.
- All tunables live in versioned `config/*.json` (no hardcoding). Secrets (`.env`, `credentials.json`,
  `token.json`) are git-ignored and never enter source control.

## Documentation

[`PRD`](docs/PRD.md) · [`PLAN`](docs/PLAN.md) · [`TODO`](docs/TODO.md) ·
[`STRATEGY`](docs/STRATEGY.md) · [`RULES_AND_AGREEMENTS`](docs/RULES_AND_AGREEMENTS.md) ·
[`INTER_GROUP_TREATY_SPEC`](docs/INTER_GROUP_TREATY_SPEC.md)

## License

MIT.
