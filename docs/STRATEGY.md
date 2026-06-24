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

## 6. The 3-variant roster (game = 3 matches)
Each variant is a distinct planner profile on the same engine:
- **aggressive** — deep search, proximity-weighted (fast capture).
- **balanced** — default weights/depth.
- **defensive / containment** — region-weighted (Devil herding; strong Thief survival when we are Angel).

## 7. Modules
`domain/strategy/features.py` (φ + flood-fill region) · `evaluation.py` (`Evaluator`) ·
`minimax.py` (`MinimaxPlanner`, alpha-beta) · `selfplay.py` (`train_weights`) ·
`servers/tools/strategy_resolver.py` (per-variant planners → treaty prose, barriers included).
