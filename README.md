# Dual AI Agent Pursuit via MCP Servers (Dec-POMDP)

Two autonomous AI agents — **the Cop** and **the Thief** — play a partially-observable
grid-pursuit game, communicating in **free natural language** over **FastMCP** servers,
orchestrated end-to-end and reported via the **Gmail API**. See [`docs/PRD.md`](docs/PRD.md),
[`docs/PLAN.md`](docs/PLAN.md), and [`docs/TODO.md`](docs/TODO.md).

## Quick start

```bash
uv sync                                            # install (uv is the only package manager)
cp .env-example .env                               # then fill in real values (see "Secrets" below)
uv run pytest                                       # full test suite (>=85% coverage gate)
uv run ruff check .                                 # zero-violation lint gate
uv run python -m cop_thief.main --mode headless --dry-run   # run a game; report to the burner sandbox
```

## Secrets & configuration

- Copy `.env-example` → `.env` and populate the real values: `DEEPSEEK_API_KEY`,
  `ANTHROPIC_API_KEY`, `COP_MCP_TOKEN`, `THIEF_MCP_TOKEN`, `GMAIL_CREDENTIALS_PATH`.
- **A zero-dependency autoloader (`src/cop_thief/config/env_loader.py`) injects `.env` into the
  environment at startup** — there is **no need to `export` or `source` anything** in your shell.
  Existing shell exports still take precedence (they are never overwritten).
- All tunable parameters live in versioned `config/*.json` (no hardcoding); secrets never enter source
  control (`credentials.json`, `token.json`, `.env` are git-ignored).

## Architecture & tooling

- **SDK boundary** — all business logic is reached through the single-entrypoint `CopThiefSDK` facade.
- **API Gatekeeper** — every external call (LLM + Gmail) is funneled through `ApiGatekeeper`: a FIFO
  backpressure queue, DeepSeek→Anthropic failover, token telemetry, and a generic
  `execute(func, *args, service, **kwargs)` chokepoint for non-LLM dispatches.
- **Strategy stack** — Tier-1 tabular **Q-Learning** (Bellman TD + ε-greedy decay), with a Tier-2
  **Conway-geometry override** that supervises the cold/uninformed Q-table.

### Offline diagnostic probe

`src/cop_thief/diagnostic_runner.py` is the permanent **offline, zero-cost** Dec-POMDP reactor probe.
It runs the real `GameLoopController` with **mocked** LLM transport (no DeepSeek/Anthropic calls),
seeded for reproducibility, and prints per-turn telemetry under a turn guillotine — use it to
regression-test pursuit math without spending API tokens:

```bash
uv run python -m cop_thief.diagnostic_runner
```

### Gmail reporting (OAuth2)

- Reports are sent via the **Gmail API** using an **OAuth2 Desktop** client (scope `gmail.modify`,
  **zero passwords**). The one-time browser consent has been completed and `token.json` is vaulted
  locally and auto-refreshed.
- **Routine runs do not re-trigger the live browser handshake** — OAuth ignition is permanently
  bypassed via the vaulted `token.json` unless the token is revoked.
- A `SubmissionSafetyGuard` interlock forces the **burner sandbox** recipient
  (`mcp.marl.telemetry@gmail.com`) under `--dry-run` so the live examiner address is never hit by accident.

## License

MIT.
