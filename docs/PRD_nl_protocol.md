# PRD (Per-Mechanism) — Natural-Language Dec-POMDP Protocol
## `marl-cop-thief` · Mechanism: Free-Language Encoder + Defensive LLM Parser

| Field | Value |
|-------|-------|
| Mechanism ID | `MECH-NL-PROTOCOL` |
| Document version | 1.00 |
| Parent docs | [`PRD.md`](./PRD.md) · [`PLAN.md`](./PLAN.md) · [`TODO.md`](./TODO.md) (Task #73, Phase 7.B/7.C) |
| Source modules | `domain/nl/encoder.py`, `domain/nl/parser.py`, `prompts/` |
| Standard | Dr. Segal *Guidelines v3.00* (§2.3, §11) |
| Status | Draft — approve before implementing Phase 7 |

> **Cardinal rule (from the brief).** Agents communicate **exclusively in free natural language**.
> A rigid, machine-parseable wire-protocol with numeric coordinates is **forbidden**. The Encoder
> turns private board state into *prose*; the Parser turns the opponent's prose back into a
> structured belief — and the agent's internal implementation is private and may differ per group.

---

## 1. Theoretical & Mathematical Background

### 1.1 Observation channel of the Dec-POMDP
In the tuple `⟨n, S, {Aᵢ}, P, R, {Ωᵢ}, O, γ⟩` (see `PRD.md §1.3`), this mechanism **is** the
observation function `O` and observation space `Ω`. Agent *i* never reads the true state `s`; it
receives a natural-language message `m_j` from agent *j* and must compute a posterior belief:
```
b_i'(s) ∝ O(m_j | s, a) · Σ_{s_prev} P(s | s_prev, a) · b_i(s_prev)
```
We do **not** maintain an explicit probability distribution over all states (intractable and
unnecessary at these grid sizes). Instead we collapse the posterior into a compact, decision-ready
**`BeliefUpdate`** sufficient statistic: estimated direction, distance band, inferred barriers, and a
scalar confidence — a deliberate, bounded approximation of the Bayesian belief update.

### 1.2 Language as a lossy, adversarial channel
The message channel is **lossy** (prose is ambiguous) and **adversarial** (the Thief may lie). The
parser is therefore designed as a *robust estimator*, not a literal translator: it must extract
signal under noise and deception, and **degrade gracefully** to a safe default rather than crash or
emit an illegal action. Confidence quantifies the trust placed in each parse and gates whether the
strategy acts on it (high confidence) or treats it as weak prior (low confidence → exploration).

### 1.3 Information value & deception
For the Thief, the message is a *control signal over the opponent's belief*: an optimal deceiver
maximises the Cop's expected belief error. For the Cop, messages carry less strategic deception
value but are used to *probe* and to coordinate the final mutually-agreed report. This asymmetry
motivates the **Tier-3 "Machiavellian Diplomat"** negotiation layer (§3).

---

## 2. The Encoder — Board State → Non-Numeric Prose

### 2.1 Functional contract
`encode(state, role, belief, style_cfg) -> str` produces a free-language message describing the
sender's situation and intent **without any machine-coordinate tokens** (no `(r,c)`, no `x=`, no JSON).

### 2.2 Prompt structure (template lives in `prompts/encoder_*.txt`, config-selected)
```
SYSTEM:
  You are {role_persona}. Speak ONLY in natural human prose. NEVER output coordinates,
  numbers-as-position, grids, JSON, or structured fields. One short paragraph.
CONTEXT (private, do NOT reveal raw values):
  - your_region:        {qualitative region, e.g. "north-east corner", "hugging the west wall"}
  - relative_to_walls:  {qualitative}
  - barriers_you_know:  {qualitative description of sealed lanes}
  - your_intent:        {pursue | evade | feint | negotiate}
  - deception_budget:   {style_cfg.deception_level}   # Thief only
STYLE:
  tone={style_cfg.tone}, verbosity={style_cfg.verbosity}, taunt={style_cfg.taunt}
TASK:
  Compose one message to your opponent that {intent-specific instruction}.
```

### 2.3 Qualitative region quantisation
The Encoder converts numeric position to **qualitative regions** before prompting (so even the prompt
holds no raw coordinates): cardinal/ordinal region buckets (N/NE/E/…/centre), wall-adjacency flags,
and "sealed-lane" descriptors derived from active barriers. Mapping thresholds are config-driven.

### 2.4 Style knobs (config `nl.encoder`)
`tone` (terse/verbose/menacing), `taunt` (bool), `deception_level` (0–1, Thief), `verbosity`. These
drive variety without ever leaking structured data.

---

## 3. Tier-3 "Machiavellian Diplomat" — State Negotiation & the Inter-Group Spite Trap

### 3.1 The Inter-Group Spite Trap (problem)
In the **bonus** inter-group series, the final score depends on **K3 mutual agreement**: if the two
groups' reports disagree, **both** score 0 for the series (`PRD.md §3.5`). A spiteful or careless
opponent can therefore weaponise disagreement — refusing to converge so that *nobody* scores ("if I
can't win, neither do you"). This is the **Spite Trap**.

### 3.2 The Diplomat strategy (mitigation)
The Diplomat is a **negotiation persona** activated during the end-of-game reconciliation phase
(and optionally for in-game truces in custom inter-group rules). It pursues a cooperative-equilibrium:
- **Disarm spite by separating outcome from record.** The agent negotiates *only the factual record*
  (what moves happened), never the *who-won framing*. Facts are anchored to the deterministic state
  machine + shared log hash (`PRD_gmail_oauth.md §4`), so there is an objective ground truth to point at.
- **Concede-the-frame, hold-the-facts.** The Diplomat is conciliatory in tone (de-escalation) while
  refusing to alter any logged fact — it offers the opponent a face-saving narrative but a
  byte-identical JSON.
- **Tit-for-two-tats fallback.** If the opponent stalls agreement, the Diplomat re-sends the canonical
  record up to `nl.diplomat.max_rounds` times with escalating clarity, then files the record with
  `mutual_agreement=false` and full logs (dispute-proof), protecting our own grade trail.

> The Diplomat **never** fabricates or bends facts to buy agreement — that would violate report
> integrity (K3/K7). It optimises *tone and framing* within the bounds of the immutable log.

---

## 4. The Parser — Opponent Prose → `BeliefUpdate` (defensive)

### 4.1 `BeliefUpdate` dataclass (output contract)
```python
@dataclass(frozen=True)
class BeliefUpdate:
    est_direction: Direction          # one of 8 compass dirs (best estimate of opponent bearing)
    distance_band: DistanceBand       # ADJACENT | NEAR | FAR | UNKNOWN
    inferred_barriers: frozenset[Cell]# walls/sealed lanes inferred from prose (may be empty)
    confidence: float                 # 0.0 – 1.0
    is_default: bool                   # True when produced by the safe fallback
    raw_excerpt: str                   # short provenance snippet for logs
```

### 4.2 Parser pipeline
```
opponent_prose
   └─▶ gatekeeper.execute(llm.parse, prompt=parser_prompt(prose))   # PRD_gatekeeper.md
        └─▶ candidate JSON-ish extraction (dir, band, barriers, confidence)
             └─▶ schema validation + range clamps
                  └─▶ confidence gate
                       ├─ conf ≥ nl.parser.min_confidence → trusted BeliefUpdate
                       └─ else / parse failure            → SAFE DEFAULT (§4.4)
```

### 4.3 Parser prompt structure (`prompts/parser_*.txt`)
```
SYSTEM:
  Extract the opponent's likely position cues from the message. Output STRICT JSON with keys:
  direction (N/NE/E/SE/S/SW/W/NW/UNKNOWN), distance_band (ADJACENT/NEAR/FAR/UNKNOWN),
  sealed_lanes (list of qualitative descriptors), confidence (0..1).
  The opponent MAY be lying or vague. If unsure, lower confidence; do not invent precision.
MESSAGE:
  {opponent_prose}
```

### 4.4 Defensive fallback (safe exploratory vector)
On **any** of: LLM error, JSON parse failure, schema violation, or `confidence < min_confidence`, the
parser returns a **safe default `BeliefUpdate`** (`is_default=True`) instead of raising:
- `est_direction` = last-known region bearing if available, else a deterministic exploration bearing.
- `distance_band = UNKNOWN`, `inferred_barriers = ∅`, `confidence = 0.0`.
This guarantees the downstream Strategy (Tier-3, `PRD_rl_qtable.md §2`) always receives a usable
belief and the turn never crashes — directly satisfying the "never crash on parse failure" mandate.

### 4.5 Deception handling
Low-confidence or internally-inconsistent prose (e.g. claims two opposite bearings) is **down-weighted**
automatically via the confidence score; the Strategy treats low-confidence beliefs as weak priors and
leans on Vision-Hunting/exploration, so a lying Thief cannot force the Cop into an illegal or losing move.

---

## 5. Functional Requirements, I/O Contracts & Metrics

### 5.1 Functional requirements
| ID | Requirement |
|----|-------------|
| NL-F1 | Encoder emits free prose, **zero** machine-coordinate tokens (validated). |
| NL-F2 | Encoder style/persona/deception are config + `prompts/` driven. |
| NL-F3 | Parser returns a `BeliefUpdate` for **every** input (never raises to caller). |
| NL-F4 | Parser confidence-gates trusted vs default beliefs. |
| NL-F5 | Safe default on failure/low-confidence (`is_default=True`). |
| NL-F6 | All LLM calls routed via the Gatekeeper (`PRD_gatekeeper.md`). |
| NL-F7 | Diplomat negotiation persona for end-game reconciliation (Spite-Trap mitigation). |
| NL-F8 | Every message + parse logged for dispute-proofing. |

### 5.2 I/O contracts
**Encoder** — In: `(BoardState, AgentRole, BeliefUpdate, style_cfg)` · Out: `str` (prose; no coords).
**Parser** — In: `str opponent_prose` · Out: `BeliefUpdate` (always valid, possibly default).

### 5.3 Performance metrics
| Metric | Target |
|--------|--------|
| Parser direction accuracy on truthful messages | ≥ 80 % (8-way) |
| Robustness: crash rate on adversarial/garbage input | **0 %** |
| Default-fallback rate on clear messages | ≤ 10 % |
| Coordinate-leak rate in encoder output | **0 %** |
| Negotiation success (agreement reached, non-spiteful opponent) | ≥ 95 % |
| Output tokens per message | ≤ `nl.encoder.max_tokens` (cost control; see `PRD_token_budget.md`) |

---

## 6. Hard Constraints, Edge Cases, Alternatives, Rationale

### 6.1 Hard constraints
- No numeric protocol anywhere on the wire (forbidden by brief).
- Parser must be total (defined for all inputs); never propagate LLM exceptions to the turn loop.
- Files ≤150 LOC; prompts externalised to `prompts/` (not hardcoded in source).

### 6.2 Edge cases
| Case | Behaviour |
|------|-----------|
| Empty / whitespace message | Safe default, `confidence=0`. |
| LLM returns malformed JSON | Extract-best-effort → on failure, safe default. |
| Contradictory bearings | Low confidence; default if below gate. |
| Out-of-range confidence | Clamp to `[0,1]`. |
| Opponent stalls agreement (Spite Trap) | Diplomat retries up to `max_rounds`, then files `mutual_agreement=false` + logs. |
| Encoder accidentally emits a number-as-position | Post-filter strips/blocks; test fails build if leaked. |

### 6.3 Alternatives considered
| Alternative | Verdict | Rationale |
|-------------|---------|-----------|
| Structured JSON game protocol | **Rejected** | Explicitly forbidden by the brief. |
| Full Bayesian belief over all states | Rejected | Intractable/overkill; compact sufficient statistic chosen. |
| Regex-only parser (no LLM) | Rejected | Brittle vs free prose & deception; LLM parser with defensive fallback chosen. |
| Hard-line negotiation (no Diplomat) | Rejected | Vulnerable to the Spite Trap; cooperative-equilibrium framing chosen. |

### 6.4 Technical rationale
Collapsing the belief into a 4-field sufficient statistic keeps decisions O(1) and testable, while the
confidence gate + safe default convert an unreliable adversarial channel into a *bounded-risk* input.
The Diplomat protects the bonus grade by attacking the real failure mode (disagreement), not the game.

---

## 7. Acceptance Criteria
- [ ] Encoder output passes the no-coordinate linter on 10⁴ random states.
- [ ] Parser returns a valid `BeliefUpdate` for every fuzzed input (0 crashes).
- [ ] Confidence gating routes low-confidence inputs to safe default.
- [ ] Diplomat reaches agreement vs cooperative opponent; files dispute trail vs spiteful one.
- [ ] All LLM calls observed passing through the Gatekeeper.
- [ ] Coverage ≥85 % for `domain/nl/*`; `ruff` clean.

## 8. Step-by-Step Test Scenarios
1. **Leak guard:** encode 1 000 random 5×5 states ⇒ assert no digit-as-coordinate / JSON token in any output.
2. **Truthful parse:** feed "I'm pinned in the south-west and you're closing from the north" ⇒ assert
   `est_direction≈N`, `distance_band≈NEAR`, `confidence ≥ min`.
3. **Garbage robustness:** feed `""`, emojis, 5 000-char noise ⇒ all return `is_default=True`, no exception.
4. **Deception:** Thief claims two opposite corners ⇒ `confidence < min` ⇒ default; Strategy explores.
5. **Barrier inference:** "I just sealed the lane to my east" ⇒ `inferred_barriers` non-empty.
6. **Gatekeeper path:** spy asserts every parse/encode LLM call invoked `gatekeeper.execute`.
7. **Spite Trap:** simulate opponent that never agrees ⇒ Diplomat retries `max_rounds`, then emits
   `mutual_agreement=false` with full logs (no fact mutation).
8. **Agreement happy path:** cooperative opponent ⇒ byte-identical record agreed within `max_rounds`.

*End of `PRD_nl_protocol.md`.*
