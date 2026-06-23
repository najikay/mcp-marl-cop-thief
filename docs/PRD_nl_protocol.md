# PRD — Natural-Language Dec-POMDP Protocol

| Field | Value |
|-------|-------|
| Mechanism | Free-text encode/parse layer + belief-driven decisions |
| Implements | PRD §F-09, KPI K1, PLAN §4 |
| Code | [`domain/nl/encoder.py`](../src/cop_thief/domain/nl/encoder.py), [`parser.py`](../src/cop_thief/domain/nl/parser.py), [`belief.py`](../src/cop_thief/domain/nl/belief.py), [`strategy/belief_strategy.py`](../src/cop_thief/domain/strategy/belief_strategy.py) |
| Version | 1.0.0 |

## 1. Purpose
Agents must coordinate using **only free natural language** — never numeric
coordinates on the wire (KPI K1). Each side encodes its situation as prose and
parses the opponent's prose back into an actionable belief.

## 2. Requirements
| ID | Requirement |
|----|-------------|
| N-1 | Outgoing messages contain **no digits / coordinates** — qualitative cues only. |
| N-2 | Incoming text is parsed into a `BeliefUpdate` (region, direction, barrier, confidence). |
| N-3 | Parsing is **defensive**: unparsable/low-signal text → zero-confidence default, never a crash. |
| N-4 | An LLM may parse (via the gatekeeper); a deterministic heuristic is the offline fallback. |
| N-5 | A belief projects to a representative cell so a strategy can act on it. |

## 3. Design
- **Encoder** (`NLEncoder.describe`) — maps the actor's cell to a region band
  (north/central/south × west/central/east) plus a movement direction, e.g.
  *"Cop: closing in from the north-west area, pressing south-east."*
- **Belief** (`BeliefUpdate`) — `region_row`, `region_col`, `moved`,
  `barrier_mentioned`, `confidence`; `estimate_cell(grid)` returns a band-centre cell.
- **Parser** (`NLParser.parse`) — tries the LLM (JSON out, via gatekeeper); on any
  failure (bad JSON, back-pressure, outage) falls back to a keyword heuristic that
  scans for region/direction/barrier cues and scores confidence.
- **Belief strategy** (`BeliefHeuristicStrategy`) — pursues/evades the *believed*
  cell only (faithful partial observability); explores toward centre when unknown.

```
state ─Encoder─▶ free-NL message ─MCP─▶ opponent
opponent text ─Parser(LLM|heuristic)─▶ BeliefUpdate ─Strategy─▶ legal Action
```

## 4. Known limitation
The belief is coarse (a 3×3 region), so two belief-only agents can stalemate
(oscillate to the move cap). Full-observability play is used where decisiveness
matters (local game, GUI); a finer belief (distance/closing cue) is future work.

## 5. Acceptance criteria
- Encoder output contains no digits (`test_nl`).
- Encode→parse round-trip recovers the region (`test_nl`).
- Noise/empty text → `BeliefUpdate.unknown()` (`test_nl`).
- LLM JSON path used when available; heuristic fallback otherwise (`test_nl_llm`).
