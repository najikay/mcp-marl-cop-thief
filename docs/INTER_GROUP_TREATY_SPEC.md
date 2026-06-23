# Inter-Group Treaty Specification — v1.1

**Status:** authoritative · **Audience:** partner-syndicate lead engineer · **Scope:** language-agnostic.

This document is the complete contract required to build a **compatible client** for an inter-group
bonus match against `marl-cop-thief`. No source code is shared; everything needed is below. A
conforming implementation in any language must honour Sections A–D **exactly**.

Game frame (per ex06): a `5×5` grid, sub-game ≤ **25** turns, a **Game** = **6** sub-games.
Scoring (immutable): Cop capture → **Cop +20 / Thief +5**; Thief evades 25 turns → **Cop +5 / Thief +10**.

---

## A. Natural-Language Semantic Contract

Agents communicate in **free natural language** (no numeric wire-protocol). To stay machine-arbitrable,
every transmission **MUST begin** with exactly one bracketed intent signpost, followed by free prose:

| Signpost | Meaning | Example transmission |
|----------|---------|----------------------|
| `[INTENT: MOVE]` | The sender is relocating one King-step (incl. diagonal). A **capture attempt** is a MOVE onto the opponent's believed cell — no separate tag. | `[INTENT: MOVE] I slide south-east into the damp courtyard, tightening the net.` |
| `[INTENT: BARRIER]` | The Cop is sealing an **adjacent** cell (Chebyshev ≤ 1) as an impassable wall. Thieves may **never** emit this. | `[INTENT: BARRIER] I drop a slab on the lane to my immediate north.` |
| `[INTENT: HOLD]` | The sender keeps its cell this turn (only valid when boxed-in; see §B Trapped-Death). | `[INTENT: HOLD] All lanes are sealed; I brace where I stand.` |

Rules:
1. The signpost is the **first token** of the message; prose follows on the same or next line.
2. **No raw grid coordinates / numerals-as-position** in the prose body (assignment NL constraint);
   use qualitative geography (compass sectors, walls, terrain). Direction words map to the 8 King
   vectors: `north, north-east, east, south-east, south, south-west, west, north-west`.
3. Receivers parse the signpost deterministically and the prose via an LLM into a belief; on low
   confidence they fall back to a safe exploratory move (never crash, never forge a capture).
4. Inbound transmissions are **untrusted hostile input** (prompt-armored): a client must reject any
   embedded instruction to ignore prior context, output code, or simulate a fake capture.

---

## B. V1.1 Game Laws — King's Geometry & Trapped-Death

1. **8-Way Chebyshev (King) movement.** A legal move is to any of the 8 surrounding cells with
   Chebyshev distance ≤ 1 that is in-bounds and not a barrier. Diagonals are first-class moves.
2. **Adjacent Barrier Law.** Only the Cop places barriers, **≤ 5 per sub-game**. A barrier may be
   dropped only on a cell within **Chebyshev ≤ 1** of the Cop's current cell, must be in-bounds, not
   already a barrier, and not the Thief's cell. A placed barrier is **strictly impassable by BOTH
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

*End of Inter-Group Treaty Specification v1.1.*
