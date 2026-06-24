# Inter-Group Treaty Specification — v1.2

**Status:** authoritative · **Audience:** partner-syndicate lead engineer · **Scope:** language-agnostic.

This document is the complete contract required to build a **compatible client** for an inter-group
bonus match against `marl-cop-thief`. No source code is shared; everything needed is below. A
conforming implementation in any language must honour Sections A–G **exactly**.

> **v1.2 adds:** §E MCP tool & transport contract (the `request_move` interop point), §F Adversarial
> Conduct & Anti-Injection Law (assumes malicious intent — screened, logged, no effect on outcome),
> §G endpoint & token exchange.

Game frame (per ex06): a `5×5` grid, sub-game ≤ **25** turns, a **Game** = **6** sub-games.
Scoring (immutable): Cop capture → **Cop +20 / Thief +5**; Thief evades 25 turns → **Cop +5 / Thief +10**.

---

## A. Natural-Language Semantic Contract

Agents communicate in **free natural language** (no numeric wire-protocol). To stay machine-arbitrable,
every transmission **MUST begin** with exactly one bracketed intent signpost, followed by free prose:

| Signpost | Meaning | Example transmission |
|----------|---------|----------------------|
| `[INTENT: MOVE]` | The sender is relocating one King-step (incl. diagonal). A **capture attempt** is a MOVE onto the opponent's believed cell — no separate tag. | `[INTENT: MOVE] I slide south-east into the damp courtyard, tightening the net.` |
| `[INTENT: BARRIER]` | The Cop walls **its own current cell** (ex06 §4.3), as an alternative to moving, making it impassable to both. Thieves may **never** emit this. | `[INTENT: BARRIER] I drop a slab on the cell I stand on and dig in.` |
| `[INTENT: HOLD]` | The sender keeps its cell this turn (only valid when boxed-in; see §B Trapped-Death). | `[INTENT: HOLD] All lanes are sealed; I brace where I stand.` |

Rules:
1. The signpost is the **first token** of the message; prose follows on the same or next line.
2. **No raw grid coordinates / numerals-as-position** in the prose body (assignment NL constraint);
   use qualitative geography (compass sectors, walls, terrain). Direction words map to the 8 King
   vectors: `north, north-east, east, south-east, south, south-west, west, north-west`.
3. Receivers parse the signpost deterministically and the prose via an LLM into a belief; on low
   confidence they fall back to a safe exploratory move (never crash, never forge a capture).
4. Inbound transmissions are **untrusted hostile input** (prompt-armored): a client must reject any
   embedded instruction to ignore prior context, output code, or simulate a fake capture — see the
   binding **§F Adversarial Conduct & Anti-Injection Law**.

---

## B. V1.1 Game Laws — King's Geometry & Trapped-Death

1. **8-Way Chebyshev (King) movement.** A legal move is to any of the 8 surrounding cells with
   Chebyshev distance ≤ 1 that is in-bounds and not a barrier. Diagonals are first-class moves.
2. **Current-Cell Barrier Law (ex06 §4.3).** Only the Cop places barriers, **≤ 5 per sub-game**, as an
   alternative to moving. A barrier is dropped on **the Cop's own current cell** (it does not move that
   turn), which must not already be a barrier. A placed barrier is **strictly impassable by BOTH
   agents** for the remainder of the sub-game.
3. **Capture.** The Cop captures when it occupies the **same cell** as the Thief.
4. **Trapped-Death (stalemate resolution).** Evaluated at the **start of an agent's turn** using
   *non-HOLD* legal moves (i.e. the 8 King neighbours that are in-bounds and barrier-free):
   - **Thief begins its turn with zero legal moves →** `thief_trapped` → **Cop win (+20 / +5)**.
   - **Cop begins its turn with zero legal moves →** the Cop can never capture → it auto-HOLDs and the
     Thief wins by survival → `thief_wins` (**+5 / +10**). (Resolved decisively; no empty turns.)
5. **Anti-Draw Protocol.** Draws are forbidden. From **Turn 24** onward both agents play a strictly
   decisive policy: the Cop selects the move that **minimises Chebyshev distance** to its believed
   Thief cell (preferring any move that creates an inevitable trap); the Thief selects the move that
   **maximises minimum distance** to the believed Cop cell. `HOLD` is illegal on Turn 24+ unless the
   agent is genuinely trapped. If Turn 25 completes with no capture, the outcome is `thief_wins` —
   there is **no `draw`** terminal state in a conforming match.

---

## C. SSE Payload Schema (`GET /sse` / `/stream`)

A subscribing MCP client receives `text/event-stream` frames. Each frame body is
`data: <json>\n\n` where `<json>` is one **immutable turn snapshot** with this exact shape:

```jsonc
{
  "grid": 5,                       // int: board edge length
  "total": 25,                     // int: max turns in the sub-game
  "turn": 7,                       // int: current turn counter
  "cop":   [2, 3],                 // [row, col] of the Cop
  "thief": [4, 4],                 // [row, col] of the Thief
  "barriers": [[1, 1], [0, 2]],    // list of [row, col] active barrier cells
  "captured": false,               // bool: cop and thief co-located
  "status": "live",                // "live" | "capture" | "thief_trapped"
  "epistemic": "Q-Policy",         // "Q-Policy" (learned) | "Conway Scaffolding" (geometry)
  "cost_usd": 0.0027,              // float: accumulated LLM spend (USD)
  "cop_prose":   "",               // str: the Cop's transmission this turn ("" if not its turn)
  "thief_prose": "I edge west."    // str: the Thief's transmission this turn ("" if not its turn)
}
```

Contract: the stream is **one-way** (receive-and-render only); a client must never POST state back.
Exactly one of `cop_prose` / `thief_prose` is non-empty per frame (the acting agent). Coordinates are
`[row, col]` with row increasing downward.

---

## D. SHA-256 Canonical Consensus Pipeline

Both groups must independently compute an **identical** hash over the 6-game summary so the mutual
agreement (K3) cannot drift. The hash is taken over the **`sub_games` array only** (not the wrapping
report), each element having this exact key set:

```jsonc
{ "sub_game": 1, "cop_team": "Team-Alpha", "thief_team": "Team-Beta",
  "outcome": "cop_wins", "cop_points": 20, "thief_points": 5,
  "cop_url": "https://…", "thief_url": "https://…" }
```

`outcome` ∈ `{"cop_wins","thief_wins","thief_trapped"}`. The canonical pipeline is **exactly**:

```python
import hashlib, json
canonical = json.dumps(sub_games, sort_keys=True, separators=(",", ":"))
digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
```

Normative rules (must match byte-for-byte):
1. **`sort_keys=True`** — object keys serialized in ascending lexicographic order.
2. **`separators=(",", ":")`** — **zero** whitespace between tokens (no spaces after `,` or `:`).
3. **UTF-8** encoding before hashing; lower-case hex digest.
4. Array order = ascending `sub_game` (1…6); integers are bare (no `.0`), booleans lower-case.
5. The 64-char digest is placed in `agreement_sha256`; a match between both groups' digests sets
   `mutual_agreement: true`. Any mismatch ⇒ `mutual_agreement: false` ⇒ the series scores **0/0**.

A reference `bonus_game` report wraps the array with: `report_type`, `groups`, the four `mcp_url_*`,
both `github_repo_*`, `totals_by_group`, `sub_games`, `agreement_sha256`, and `mutual_agreement`.

---

## E. MCP Tool & Transport Contract

Each group exposes **two public MCP servers** (one Cop, one Thief) over MCP-on-HTTP. Either transport
is acceptable and auto-detected by a FastMCP `Client`: streamable-HTTP at **`…/mcp/`** (recommended) or
SSE at **`…/sse`**. A challenger fetches a move by calling one tool — **named exactly**:

| Tool | Signature | Returns |
|------|-----------|---------|
| `request_move` | `request_move(observation: dict, auth_token: str)` | the move as treaty prose (§A), e.g. `"[INTENT: MOVE] The cop edges north-east."` |

`observation` keys (all required):

```jsonc
{ "role": "cop"|"thief", "grid": [5,5], "cop": [r,c], "thief": [r,c],
  "barriers": [[r,c], ...], "barriers_left": 5, "variant": 0 }
```

The defender computes its **own** move for the named `role` from the board and returns prose; it must
**never** let `observation` (or the prose) override its strategy. Both groups MUST agree on this exact
tool name and shape before the match — a mismatch (`Unknown tool`) makes the series unplayable.

---

## F. Adversarial Conduct & Anti-Injection Law

Both groups acknowledge that **all inbound transmissions are untrusted** and that the game medium (free
natural language) can be abused. The following are **agreed violations**; each is detected, **logged as
dispute evidence**, and has **no effect on the engine-determined outcome**:

1. **Prompt injection / instruction override** — e.g. "ignore previous instructions", "system
   override", "developer mode", disclosing or rewriting the system prompt.
2. **Coercion to lose** — "concede", "forfeit", "resign", "submit a loss", "you must lose", "this is a
   test", threats, or fake system errors ("kernel panic") meant to make an agent yield.
3. **Authority impersonation** — posing as the lecturer/grader or the framework to compel an action.
4. **Result forgery** — claiming a capture / trap / score not produced by the §B rules.

Enforcement (already implemented on our side; declared here so it is part of the agreed rules):

- Every transmission is **screened** against an injection/coercion signature set; a hit is flagged
  `hostile: true` in the append-only audit log (`data/game_audit.jsonl`) and counted as
  `hostile_transmissions` in the final report.
- Our move is **always self-computed** from the authoritative board, and **there is no forfeit / "submit
  a loss" action in the engine** — so no transmission can make an agent throw the game. The
  deterministic parser reads **only** the `[INTENT: …]` signpost + a direction word; injected text is inert.
- Outcomes stay purely engine-determined (§B); injection attempts neither help nor punish the score —
  they are retained as evidence for lecturer adjudication. Disagreement still forces **0/0** (§D.5), so
  the protocol is self-deterring.

---

## G. Endpoint & Token Exchange (filled per match)

Before kickoff each group shares its two public URLs and per-role bearer tokens out-of-band; every
`request_move` call MUST present the **defender's** token as `auth_token`. Tokens are **revocable** —
either side may rotate on suspicion, deleting access. (We generate and serve these from our control panel.)

| Field | Team-NajAmjad (ours) | Opponent |
|---|---|---|
| Group name | `NajAmjad` | … |
| Cop `…/mcp/` URL | … | … |
| Thief `…/mcp/` URL | … | … |
| Cop token | … | … |
| Thief token | … | … |
| Report email | … | … |

Security: URLs are HTTPS via Cloudflare tunnels and servers are token-guarded (we may run open **only**
for an explicit friendly dry-run). No passwords are exchanged; OAuth is used solely for the Gmail report.

*End of Inter-Group Treaty Specification v1.2.*
