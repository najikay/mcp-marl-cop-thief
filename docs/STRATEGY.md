# Strategy: Angel–Devil Minimax with Self-Play RL

> Dr. Segal's brief: *"use game theory … reinforcement learning is the key to winning … the
> one in the assignment is the most basic."* This is our answer — a single coherent engine
> combining **game theory**, the **Conway Angel–Devil** blocking game, and **advanced
> (function-approximation, self-play) RL**, all numpy-only.

## 1. Framing — a zero-sum Markov game
The sub-game is a two-player zero-sum **Markov game** ⟨S, A_cop, A_thief, P, R⟩. The Cop maximizes,
the Thief minimizes a single cop-signed value. This is the principled multi-agent generalization of
the single-agent Q-learning in the assignment.

## 2. Game theory — depth-limited alpha-beta minimax
At decision time the acting side runs **alpha-beta** to depth *D* over the real transition function
(`state.apply_action`), assuming an **optimal adversary** at every ply. Terminal scores are
capture / `thief_trapped` (`+WIN − turns`, sooner is better) and evasion / cop-trapped
(`−WIN + turns`). Non-terminal leaves use the linear evaluation (§4). Because every leaf rewards
*progress*, the policy never stalls → **draws are structurally avoided** (Dr. Segal's requirement).

## 3. Angel–Devil — Conway's blocking game
This maps the assignment's "Angel/Devil" onto **Conway's Angel problem**: the **Thief is the Angel**
(escapes on the grid), the **Cop is the Devil** (drops walls — §4.3, on its *own current cell* — to
trap it). The Cop's action set in the search therefore includes `PLACE_BARRIER(self)`, so the planner
**discovers herding-to-trap lines on its own** — no hand-coded barrier heuristic. The evaluation's
*containment* term (the Angel's free reachable region, by flood fill) is exactly the Devil's objective.

## 4. Evaluation (cop-positive, linear, learnable)
`value(s) = w · φ(s)` with features φ (each ~[0,1], higher = better for Cop):

| feature | meaning |
|---|---|
| proximity | `1 − chebyshev(cop,thief)/diag` — Cop closes in |
| containment | `1 − thief_region/area` — shrink the Angel's escape region |
| immobilization | `1 − thief_mobility/8` — fewer Thief moves |
| resources | `barriers_left/5` — keep Devil optionality |

## 5. Advanced RL — self-play TD weight learning
The weights **w** are not hand-fixed; they are learned by **self-play**: both sides act by minimax
over the *current* weights (ε-exploration for coverage), and **w** is updated by a bounded TD/MC rule
toward minimax-backed game outcomes (Angel-vs-Devil co-evolution). This is value-function
approximation with a minimax backup — genuinely beyond tabular Q. `train_weights()` returns the
learned vector; live play uses tuned defaults and can adopt learned weights.

## 6. Beating a sub-optimal opponent — risk knob + opponent model
Pure minimax is **safe** (unexploitable) but assumes a perfect adversary, so it won't *exploit* a weak
one. We add a **pessimism knob** that interpolates the opponent's node between their optimal reply
(`pessimism = 1` → minimax) and the average over their legal moves (`pessimism = 0` → expectimax that
exploits). An online **`OpponentModel`** judges each observed opponent move by a cheap geometric proxy
(did the Thief flee / the Cop close in?) and sets `pessimism` to the running **rational-rate**: an
optimal opponent → pessimism→1 (stay safe); a sloppy/random one → pessimism↓ (exploit). This is the
game-theory distinction between **maximin (Nash, unexploitable)** and **best-response (exploiting)** —
and it needs no training, just observation across the 6 sub-games.

## 7. The 3-variant roster (game = 3 matches)
Each variant is a distinct profile on the same engine, differing in depth, weights, and **risk**
(how far it trusts the opponent model to lower pessimism):
- **aggressive** — `risk = 1` (fully exploits a weak opponent), proximity-weighted.
- **balanced** — `risk = 0.5`, default weights.
- **defensive / containment** — `risk = 0` (pure minimax, never exploitable), region-weighted (Devil herding).

## 8. Random openings (ex06 §4.2)
Each sub-game starts from a **seeded-random** Cop/Thief placement (config `game.start_mode = "random"`,
`game.random_seed`), so play generalizes beyond a fixed corner opening — and the self-play RL trains on
varied openings (more robust weights). The seed is deterministic, so both groups reproduce the identical
opening per sub-game (the agreed result cannot drift).

## 9. Modules
`domain/strategy/features.py` (φ + flood-fill region) · `evaluation.py` (`Evaluator`) ·
`minimax.py` (`MinimaxPlanner`, minimax/expectimax) · `opponent.py` (`OpponentModel`) ·
`selfplay.py` (`train_weights`) · `domain/geometry.py` (`random_start_positions`) ·
`servers/tools/strategy_resolver.py` (per-variant planners + opponent model → treaty prose).
