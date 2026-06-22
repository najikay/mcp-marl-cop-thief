# Bonus — Inter-Group Competition: Coordination Guide

This document is the **shared contract** between the two groups that play a bonus
series together. Both groups build their systems independently; the only things
that must match are (1) the MCP tool interface, (2) the natural-language
discipline, and (3) the final report. Agree on everything here *before* playing.

> Our group: **Team-Alpha** (Amjad + Naji). Partner group: **Team-Beta** (the
> other pair). Swap the names/URLs below for the real ones.

---

## 1. What the bonus is (lecture §12, PRD §3.5)

- A **series = 6 sub-games** between two groups, with a **role swap**:
  - Sub-games **1–3**: Team-Alpha's **Cop** vs Team-Beta's **Thief**.
  - Sub-games **4–6**: Team-Beta's **Cop** vs Team-Alpha's **Thief**.
- Each group's points are tallied across both halves into `totals_by_group`.
- **Scoring per series:** higher total → **10**, loser → **7**, exact tie → **5** each.
- **Final bonus** = average over all valid series you play (e.g. winning one of
  two series → `(10 + 7) / 2 = 8.5`). Playing more than one partner is allowed.
- **Each group emails its OWN report**, and the two reports must describe the
  **exact same result** (`mutual_agreement: true`). **If they disagree → series
  cancelled → 0 for both.** This is the single most important rule.
- Deadline: within one week of the assignment being published.

## 2. The MCP tool contract (must be identical on both sides)

Each group exposes **two** MCP servers — one Cop, one Thief — at public URLs.
Every group's servers MUST expose these tools with these exact names and
payloads, so either group's orchestrator can drive either group's servers.

| Tool | Input | Output | Notes |
|------|-------|--------|-------|
| `start_sub_game` | `{ "sub_game_id": str, "grid_size": [r,c], "max_moves": int, "max_barriers": int, "start": {"self": null, "opponent": null} }` | `{ "ok": true }` | Resets the agent's belief. Positions are assigned by the **orchestrator**, never exchanged as coords between agents. |
| `receive_message` | `{ "sub_game_id": str, "text": str }` | `{ "ok": true }` | Free natural-language text from the opponent. Updates belief. |
| `propose_action` | `{ "sub_game_id": str }` | `{ "action": "move"\|"place_barrier", "direction": "N\|NE\|E\|SE\|S\|SW\|W\|NW\|STAY", "message": str }` | The agent's move **and** its outgoing free-NL message. Thief must never return `place_barrier`. |
| `agree_on_report` | `{ "report": {...} }` | `{ "agree": bool }` | Mutual-agreement handshake on the final JSON. |

**Hard rules for `message` / `receive_message`:**
- Free natural language **only** — no coordinates, no JSON, no rigid codes
  (PRD KPI K1). "I'm hugging the eastern wall, pressing south" is valid;
  "(4,1)->S" is **not**.
- The receiver parses prose into a belief with its own LLM/heuristic. Each side's
  parser must tolerate the *other* group's phrasing, not just its own encoder.

> In this repo the contract is mirrored by `NLEncoder.describe` (produces the
> `message`) and `NLParser.parse` (consumes `receive_message`). Keep both groups'
> phrasing within the compass-direction + region vocabulary so parsing is robust.

## 3. Who runs the match

Exactly **one** orchestrator drives a sub-game (the MCP *client*). Decide per
sub-game which group's orchestrator is in charge — it calls `propose_action` on
the side to move, relays the returned `message` to the other side via
`receive_message`, applies the move on its own authoritative board, and records
the outcome. Both groups must run the **same rules and scoring** (this repo's
`config/setup.json` values: 5×5, 25 moves, 6 sub-games, 5 barriers, 20/10/5/5)
so the authoritative result is reproducible.

## 4. The report both groups send (schema in `bonus_report.py`)

Both groups send the **same** JSON body (only the `mutual_agreement` handshake
confirms it). Key fields: `report_type: "bonus_game"`, `groups`, two
`github_repo_*`, four `mcp_url_*` (cop/thief per group), `students_group_1/2`,
`sub_games` (each tagged with `cop_group`/`thief_group`/outcome/scores),
`totals_by_group`, `bonus_claim`, `mutual_agreement`.

Email destination: `rmisegal+uoh26b@gmail.com`, **JSON body only, no free text.**

## 5. Agreement checklist (do this before sending)

1. Both orchestrators produced the **same `totals_by_group`** and the same
   per-sub-game outcomes. Use `AgreementReconciler.reconcile(a, b)` — it compares
   exactly the result-bearing fields.
2. `bonus_claim` derived from those totals matches on both sides
   (`compute_bonus_claim`).
3. Both set `mutual_agreement: true` only after 1–2 pass.
4. Each group sends its own email. If anything diverges, **do not send** — fix
   the mismatch first, or the series scores 0/0.

## 6. Pre-match readiness (both groups)

- [ ] Two public MCP URLs each (cop + thief), token-protected and revocable.
- [ ] Tool names/payloads match §2 exactly.
- [ ] Same `config/setup.json` rule values.
- [ ] Gmail OAuth reporter ready (JSON-only body).
- [ ] Dry-run one full 6-sub-game series; confirm `reconcile` returns `true`.
