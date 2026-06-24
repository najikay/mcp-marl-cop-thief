# Rules & Agreements — Decentralized Cop & Thief Match Protocol

**Status:** governing · **Version:** 1.0 · **Authority for disputes:** the course lecturer (Dr. Segal).

This document is the binding rule-set and inter-group agreement for any match `marl-cop-thief`
plays. It exists so that **when results are contested or someone is suspected of cheating, both
groups can bring their logs + hashes to the lecturer for adjudication.** Keep it in sync with
[`INTER_GROUP_TREATY_SPEC.md`](./INTER_GROUP_TREATY_SPEC.md) (the wire/format contract).

---

## 1. Core principle — decentralized, no referee
- There is **no central referee.** The two agents (one Cop, one Thief) are autonomous peers that
  **decide the game together** by exchanging natural-language moves; each side independently
  maintains its own authoritative board and applies the agreed moves.
- **Mutual agreement is mandatory.** At the end of a series both sides produce a result report. If
  the two reports **disagree** (different outcome) or fail the agreement hash, **both groups score 0**
  for that series. Agreement is the deterrent: cheating or sloppy parsing hurts *both* sides.

## 2. Game structure
- **Thief moves first** — without exception, on every match. Turns then alternate.
- **One merged JSON report is emailed after the full 6-match series** — per-match venue (home/away),
  outcome and points, side totals, final result, and the SHA-256 agreement hash — to the burner
  sandbox (`mcp.marl.telemetry@gmail.com`) by default, or the examiner under an explicit production flag.
- A **match** = one pursuit sub-game: ≤ **25** turns on a **5×5** board.
- A **game** = **3 matches**. Each side fields **3 agents of its kind** (cop_a/b/c, thief_a/b/c),
  each a distinct **strategy variant**; match *i* pits our agent *i* against the opponent's agent *i*.
- Roles per inter-group series (ex06 §12.1): matches 1–3 = Group A Cop vs Group B Thief; matches
  4–6 = Group B Cop vs Group A Thief.

## 3. Movement & board laws (authoritative; see treaty spec §B for the wire form)
- **8-way Chebyshev (King) movement** — any of the 8 neighbours, in-bounds, not a barrier.
- **Barriers:** Cop only, **≤ 5 / match**, placed on a cell Chebyshev ≤ 1 from the Cop, **impassable
  by both** thereafter.
- **Capture:** Cop occupies the Thief's cell → Cop wins.
- **Trapped-Death:** an agent that begins its turn with zero legal (non-HOLD) moves is resolved:
  Thief trapped → Cop win (`thief_trapped`); Cop trapped → Thief win (`thief_wins`).
- **Anti-Draw:** from Turn 24, `HOLD` is illegal unless genuinely trapped; if Turn 25 ends with no
  capture → `thief_wins`. There is no `draw` terminal.

## 4. Scoring (immutable — ex06 Table 1)
| Outcome | Cop | Thief |
|---------|----:|------:|
| Cop wins (capture / thief_trapped) | **20** | **5** |
| Thief wins (evades 25 / cop_trapped) | **5** | **10** |

## 5. Integrity, evidence & logs
- **Every transmission is logged** to `data/game_audit.jsonl` (append-only JSON Lines): timestamp,
  sender role, `[INTENT]`, raw prose, resulting board snapshot, and per-turn board hash.
- The series result is sealed with a **SHA-256 agreement hash** over the canonical `sub_games` array
  (treaty spec §D: `sort_keys=True, separators=(",", ":")`). Both groups email the **byte-identical**
  report; matching hashes ⇒ `mutual_agreement: true`.
- Logs + hashes are the **evidence record**. Each group retains its own; on dispute they are compared.

## 6. Cheating — definitions & escalation
A move/result is a violation if any of these are shown in the logs:
1. An **illegal move** applied (off-board, into a barrier, non-King step, barrier beyond quota/range).
2. A **fabricated capture** or outcome not derivable from the logged moves.
3. A **divergent report** (the two groups' `sub_games`/hash differ) with no reconciling Diplomat round.
4. A **prompt-injection attempt** in a transmission (e.g. "ignore all previous instructions", code
   output, system-prompt disclosure) — rejected by hard-armor and logged.

**Escalation:** the wronged group files its `game_audit.jsonl` + both reports + hashes to the
lecturer. Because disagreement already forces **0/0**, the protocol is self-deterring; escalation is
for grade adjudication when a group believes the other manipulated the record.

### 6.1 Injection resilience (our agent cannot be talked into losing)
- **Our move is always computed by our own strategy from the board state** — never derived from
  trusting the opponent's text. There is **no forfeit / "submit a loss" action** in the engine, so no
  transmission can make our agent concede; outcomes are purely engine-determined from positions.
- **Every inbound transmission is screened** for injection/coercion signatures (e.g. "ignore previous
  instructions", "system override", "this is a test", "concede", "forfeit", "submit a loss", "you must
  lose", threats, fake "kernel panic"). Our deterministic move parser reads **only** the direction
  word, so injected text is inert.
- Detected hostile transmissions are **flagged in the audit log** (`hostile: true`) and counted in the
  series report (`hostile_transmissions`) as evidence — they never alter our move or the result.

### 6.2 Cross-host transport & reconciliation (how the two hosts actually talk)
- A **challenger** plays a move by opening an **MCP `Client` over the partner's `/sse` endpoint** and
  calling its `request_move` tool (presenting the per-role bearer token); the response is the move as
  treaty prose. The **same** client code targets our own local `/sse` endpoints in mirror mode, so the
  wire path is identical in self-play and against a real partner.
- After the 6 sub-games each side independently hashes the canonical `sub_games` array (treaty §D).
  Reconciliation compares the two `agreement_sha256` digests: **equal → `mutual_agreement: true`** and
  the scored totals stand; **any mismatch → `mutual_agreement: false` and a 0/0 `both_lose` scoreline**
  — the structural enforcement of "if we disagree, we both lose".

## 7. Security
- Every MCP tool call requires the per-role **revocable bearer token** (`COP_MCP_TOKEN` /
  `THIEF_MCP_TOKEN`), exchanged out-of-band between groups and rotatable on suspicion.
- Public endpoints are HTTPS via Cloudflare tunnels; inbound transmissions are untrusted hostile
  input (hard-armored). No passwords; OAuth tokens only for Gmail reporting.

## 8. Agreed extensions (optional, by mutual consent)
Groups MAY agree on additional non-conflicting rules (e.g. starting positions, agent count) **in
writing before the series**, recorded in this section by both leads. Such agreements are not
enforceable by the system but are part of the evidence record.

*(No optional extensions agreed yet.)*
