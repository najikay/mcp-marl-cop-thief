# PRD (Per-Mechanism) — Tabular Q-Learning Strategy
## `marl-cop-thief` · Mechanism: Reinforcement-Learning Decision Engine

| Field | Value |
|-------|-------|
| Mechanism ID | `MECH-RL-QTABLE` |
| Document version | 1.00 |
| Parent docs | [`PRD.md`](./PRD.md) · [`PLAN.md`](./PLAN.md) · [`TODO.md`](./TODO.md) (Task #74, Phase 7.E) |
| Source modules | `domain/strategy/base_strategy.py`, `domain/strategy/heuristic_strategy.py`, `domain/strategy/qlearning_strategy.py` |
| Standard | Dr. Segal *Guidelines v3.00* (§2.3 per-mechanism PRD, §11 metrics) |
| Status | Draft — approve before implementing Phase 7.D/7.E |

> **Scope note.** Per the brief, reinforcement learning is **optional and recommended**, not
> mandatory. When enabled, **only tabular Q-Learning** is permitted (no neural networks). This PRD
> specifies a **three-tier strategy stack** so the agent is always able to act legally even when the
> Q-table is uninformed.

---

## 1. Theoretical & Mathematical Background

### 1.1 The pursuit as an MDP slice of the Dec-POMDP
The full game is a Dec-POMDP `⟨n, S, {Aᵢ}, P, R, {Ωᵢ}, O, γ⟩` (see `PRD.md §1.3`). Each agent's
*decision* sub-problem, conditioned on its current **belief** of the world, is treated as a
single-agent MDP `⟨S, A, P, R, γ⟩`. Tabular Q-Learning is an **off-policy, model-free, temporal-
difference (TD)** control method that learns the optimal action-value function `Q*(s,a)` without
knowing `P` or `R` in closed form — it learns purely from sampled transitions
`(s, a, r, s′, done)` collected over **episodes**.

### 1.2 Action-value function
`Q(s,a)` is the expected discounted return of taking action `a` in state `s` and then acting
greedily:
```
Q*(s,a) = E[ Σ_{k=0}^{∞} γ^k · r_{t+k+1} | s_t = s, a_t = a ]
```

### 1.3 Bellman optimality update (the learning rule — written in full)
On each sampled transition the table is updated by the **Bellman TD update**:
```
                 ┌                                                  ┐
Q(s,a) ← Q(s,a) + α · │ r + γ · max_{a′} Q(s′,a′) · (1 − done) − Q(s,a) │
                 └                                                  ┘
```
Decomposed into the two quantities the implementation computes explicitly:
```
TD_target = r + γ · ( 0 if done else max_{a′} Q(s′, a′) )
TD_error  = TD_target − Q(s, a)
Q(s, a)  += α · TD_error
```
- `α` — **learning rate** (config `rl.alpha`, default `0.1`, valid range `[0.01, 0.5]`): how strongly
  new information overrides the stored estimate.
- `γ` — **discount factor** (config `rl.gamma`, default `0.9`, valid range `[0, 1]`): weight of future
  reward vs immediate reward.
- `done` — terminal flag: at a terminal state there is no bootstrap (`max_{a′}Q(s′,a′)` is masked to 0).

Reference minimal kernel (matches the assignment's worked example):
```python
best_next_q = 0.0 if done else float(np.max(q_table[next_state]))
td_target   = reward + discount_factor * best_next_q
td_error    = td_target - q_table[state, action]
q_table[state, action] += learning_rate * td_error
```

### 1.4 Epsilon-Greedy exploration with decay (written in full)
Action selection balances exploration vs exploitation:
```
            ┌ random legal action a ∈ A_legal(s)        with probability ε_t
π(s) =      │
            └ argmax_{a ∈ A_legal(s)} Q(s, a)           with probability 1 − ε_t
```
The exploration rate **decays per episode** (exponential schedule, config-driven):
```
ε_t = max( ε_min , ε_start · (ε_decay)^t )
```
- `ε_start` (config `rl.epsilon_start`, default `1.0`)
- `ε_min`   (config `rl.epsilon_min`, default `0.05`)
- `ε_decay` (config `rl.epsilon_decay`, default `0.995`, applied once per completed episode `t`)

> Linear-decay alternative `ε_t = max(ε_min, ε_start − t·δ)` is supported via
> `rl.epsilon_schedule = "linear"` but exponential is the default (smoother late-stage annealing).

### 1.5 Convergence assumptions
Tabular Q-Learning converges to `Q*` w.p. 1 provided: (a) every `(s,a)` is visited infinitely often
(guaranteed in the limit by `ε_min > 0`), and (b) the Robbins-Monro step-size conditions
(`Σα = ∞`, `Σα² < ∞`) are approximately honoured. On the small grids here (2×2…5×5) the table is
tiny and converges quickly.

---

## 2. The Three-Tier Strategy Stack

Decisions cascade through tiers; a tier is used only if the tier above abstains. This guarantees a
**legal action is always produced** and directly serves PRD KPI **K5 (draw avoidance)**.

| Tier | Name | Trigger | Behaviour |
|------|------|---------|-----------|
| **Tier 1** | **Q-Table (learned)** | `max_a Q(s,·)` has a confident, non-degenerate maximum (spread ≥ `rl.q_confidence_margin`) | Pick `argmax_a Q(s,a)` over legal actions (ε-greedy during training). |
| **Tier 2** | **Vision-Hunting hybrid fallback** | Q-row is uninformed/flat **or** state unseen, **and** opponent is within the vision band | Deterministic distance-driven move: Cop **minimises** Chebyshev distance to the believed thief cell (and uses barriers to cut escape lanes); Thief **maximises** distance / heads to the largest open region. |
| **Tier 3** | **Safe exploratory vector** | No learned value **and** opponent outside vision band (no signal) | Structured exploration toward the last-known region / unexplored cells; never a no-op that risks a draw. |

### 2.1 Tier 2 — "Vision-Hunting" (detailed)
When the Q-table cannot discriminate (cold start, unseen state, or `max−2ⁿᵈ` value spread below
`rl.q_confidence_margin`), the agent falls back to a **greedy geometric controller** seeded by the
current `BeliefUpdate` (see `PRD_nl_protocol.md`):
- **Cop:** choose the legal move minimising `chebyshev(cop, belief.est_thief_cell)`; ties broken by
  the immutable tie-break order (deterministic, draw-avoiding). If a barrier placement reduces the
  thief's legal-escape count by ≥ `rl.barrier_value_threshold` and quota remains, place a barrier.
- **Thief:** choose the legal move maximising minimum distance to the believed cop cell, biased
  toward the cell with the most onward legal moves (avoid being cornered).

Vision-Hunting both **acts well immediately** and **generates high-quality transitions** that the
Q-table learns from, accelerating Tier-1 takeover.

---

## 3. State-Space Index Mapping (positions + active barriers)

### 3.1 Encoding contract
The Q-table is a 2-D array `q_table[state_index, action_index]`. State index is a **bijective
flattening** of the agent-relevant state. For grid `R×C` (`N = R·C` cells):

```
cop_idx    = cop_row    * C + cop_col           ∈ [0, N)
thief_idx  = thief_row  * C + thief_col         ∈ [0, N)
barrier_sig = canonical_barrier_signature(barriers)   # see §3.2
state_index = (cop_idx * N + thief_idx) * B + barrier_bucket(barrier_sig)
```
- `action_index ∈ [0, |A|)`: 8 movement directions + STAY (= 9) for the Thief; +1 PLACE_BARRIER
  (= 10) for the Cop. Action enums are config-frozen (`constants.py`).
- All of `R, C, |A|, B` come from **config**, never literals (Guideline E6 / §7.2).

### 3.2 Barrier signature & bucketing
Active barriers are a `frozenset` of occupied cells. To keep the table tabular and bounded:
- **Exact mode** (`rl.barrier_mode="exact"`, small grids): `barrier_sig` is the integer bitmask over
  `N` cells; `B = 2^N`. Only enabled for `N ≤ rl.exact_barrier_max_cells` (default 9, i.e. ≤3×3) to
  avoid table blow-up.
- **Bucketed mode** (`rl.barrier_mode="bucketed"`, default for 4×4/5×5): `barrier_bucket` =
  `min(count_active_barriers, max_barriers)` ⇒ `B = max_barriers + 1`. This trades exact wall layout
  for barrier-count abstraction, keeping the table at `N² · (max_barriers+1)` rows
  (5×5: `625 · 6 = 3 750` rows — trivial).

### 3.3 Worked size example (5×5, bucketed)
`N=25`, `|A_cop|=10`, `B=6` ⇒ Cop table = `25·25·6 × 10 = 3 750 × 10 = 37 500` cells. Fits in memory
trivially; serialised to `results/q_table_cop.npy` / `q_table_thief.npy`.

---

## 4. Reward Shaping

Values are config-sourced (`config/setup.json → rl.rewards`) and **aligned to the immutable scoring
matrix** so the learned policy optimises the actual objective.

| Event | Symbol | Default | Rationale |
|-------|--------|---------|-----------|
| **Capture** (terminal, Cop perspective) | `r_capture` | **+20** | Mirrors `scoring.cop_win`; the goal signal. |
| **Evasion** (terminal, Thief perspective) | `r_evasion` | **+10** | Mirrors `scoring.thief_win`. |
| **Step penalty** (per non-terminal move) | `r_step` | **−1** | Pressures the Cop to capture quickly; discourages dithering/draws. |
| **Invalid-move penalty** (rejected action) | `r_invalid` | **−5** | Teaches legality; large fall-into-pit analogue from the brief. |
| **Caught** (terminal, Thief perspective) | `r_caught` | **−10** | Symmetric negative for the evader. |
| **Cornered shaping** (optional) | `r_corner` | **−0.5** | Small shaping if legal-move count drops below threshold. |

> The invalid-move penalty is defensive only: in production the RulesEngine prevents illegal actions
> from being *applied*; the penalty exists for training robustness when exploring random actions.

---

## 5. Functional Requirements & I/O Contracts

### 5.1 Functional requirements
| ID | Requirement |
|----|-------------|
| RL-F1 | `BaseStrategy.choose_action(belief, state, role) -> Action` returns a **legal** action always. |
| RL-F2 | `QLearningStrategy` implements Tier-1 ε-greedy selection + Bellman `update()`. |
| RL-F3 | Tier-2 Vision-Hunting fallback engages on cold/flat Q-rows within vision band. |
| RL-F4 | Tier-3 safe exploration engages when there is no usable signal. |
| RL-F5 | State indexing per §3; action enums config-frozen. |
| RL-F6 | Q-tables persist to / load from `results/` (per role). |
| RL-F7 | ε decays per episode per §1.4; α, γ clamped to valid ranges. |
| RL-F8 | All hyper-parameters & rewards are config-sourced (no hardcoding). |

### 5.2 Data contracts
**`choose_action` Input**
| Field | Type | Constraint |
|-------|------|-----------|
| `belief` | `BeliefUpdate` | from NL parser (`PRD_nl_protocol.md`) |
| `state` | `BoardState` | current legal state |
| `role` | `AgentRole` | COP / THIEF |

**`choose_action` Output**
| Field | Type | Constraint |
|-------|------|-----------|
| `action` | `Action(type, direction?)` | must pass `RulesEngine.validate` |
| `meta.tier` | `int` | 1/2/3 — which tier produced the action (telemetry) |

**`update` Input:** `(state_index:int, action_index:int, reward:float, next_state_index:int, done:bool)`
**`update` Output:** mutated Q-table cell; returns `td_error:float` for monitoring.

### 5.3 Performance metrics
| Metric | Target |
|--------|--------|
| Cop capture rate after training (5×5) | ≥ 60 % vs heuristic thief |
| Tier-1 takeover (share of decisions from Q-table) by end of training | ≥ 70 % |
| Mean episode length trend | monotonically **decreasing** for the Cop (faster captures) |
| Decision latency | ≤ 1 ms per `choose_action` (pure table/geometry; no network) |
| Draw rate | **0 %** (K5) |

---

## 6. Hard Constraints, Edge Cases, Alternatives, Rationale

### 6.1 Hard constraints
- Tabular only — **no** NN, no GPU, no deep-RL libs.
- Files ≤150 LOC each (split learner / selector / indexer if needed).
- No hardcoded hyper-parameters, grid sizes, or rewards.
- Action set frozen in `constants.py`; thief has no PLACE_BARRIER.

### 6.2 Edge-case behavioural definitions
| Edge case | Defined behaviour |
|-----------|-------------------|
| Unseen state | Lazily initialise Q-row to zeros → Tier-2/3 fallback. |
| Flat/tied Q-row (`max−2nd < margin`) | Treat as uninformed → Tier-2. |
| `done = True` | Mask bootstrap (`max_{a′}Q = 0`); apply terminal reward. |
| No legal moves except STAY | Return STAY only if non-losing; else accept forced terminal (never crash). |
| Barrier quota exhausted (Cop) | PLACE_BARRIER pruned from `A_legal`. |
| Corrupt/missing saved table | Re-initialise to zeros; log a warning; continue (graceful degradation). |
| α/γ/ε out of range in config | Clamp to valid range + log; never raise mid-game. |

### 6.3 Alternatives considered
| Alternative | Verdict | Rationale |
|-------------|---------|-----------|
| DQN / neural Q | Rejected | Out of scope; needs training infra/GPU; brief forbids. |
| SARSA (on-policy) | Considered | Q-Learning chosen for off-policy sample efficiency + matches brief's worked example. |
| Pure heuristic (no RL) | Allowed fallback | Used as Tier-2/3; but RL demonstrates adaptive play, the grading differentiator. |
| Exact-barrier indexing on 5×5 | Rejected | `2²⁵` blow-up; bucketed abstraction chosen (§3.2). |

### 6.4 Technical rationale
The three-tier stack guarantees **always-legal, never-draw** behaviour during the cold-start phase
while the Q-table is still learning, and Vision-Hunting simultaneously *teaches* the table good
transitions — so Tier-1 takes over quickly with minimal episodes, on tiny tables that fit trivially
in memory.

---

## 7. Acceptance Criteria
- [ ] Single Bellman update reproduces the worked example numerically.
- [ ] ε-decay follows the configured schedule; clamps at `ε_min`.
- [ ] State indexing is bijective (round-trip encode/decode) for all supported grids.
- [ ] Every `choose_action` output passes `RulesEngine.validate`.
- [ ] Draw rate = 0 % over the sanity suite.
- [ ] Hyper-parameters/rewards entirely config-sourced (hardcode scan clean).
- [ ] Coverage ≥85 % for `domain/strategy/*`; `ruff` clean.

## 8. Step-by-Step Test Scenarios
1. **Bellman math:** given `Q(s,a)=0.5, r=−1, γ=0.9, max Q(s′)=2.0, α=0.1, done=False` ⇒ assert
   `td_target = 0.8`, `td_error = 0.3`, `Q(s,a)=0.53`.
2. **Terminal mask:** same with `done=True` ⇒ `td_target = −1`, `Q(s,a)=0.35`.
3. **ε-decay:** start 1.0, decay 0.995, min 0.05 ⇒ assert `ε` at episodes 0/100/2000 and floor at 0.05.
4. **Index bijection:** for 2×2,3×3,5×5 random states, `decode(encode(s)) == s`.
5. **Tier cascade:** zeroed table within vision band ⇒ `meta.tier == 2`; outside band ⇒ `tier == 3`;
   after training a clear max ⇒ `tier == 1`.
6. **Legality fuzz:** 10⁴ random states ⇒ all returned actions legal; thief never returns PLACE_BARRIER.
7. **Convergence (toy 2×2):** train N episodes ⇒ Cop mean episode length decreases; capture rate ≥ target.
8. **Resilience:** corrupt `q_table_cop.npy` ⇒ re-init + warning, game still runs.

*End of `PRD_rl_qtable.md`.*
