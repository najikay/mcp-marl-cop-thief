# PRD — Tabular Q-Learning Strategy

| Field | Value |
|-------|-------|
| Mechanism | Tabular Q-Learning pursuer (optional adaptive strategy) |
| Implements | PRD §F-10, §6 (RL = tabular only), PLAN Phase 7.E |
| Code | [`domain/strategy/qtable.py`](../src/cop_thief/domain/strategy/qtable.py), [`qlearning_strategy.py`](../src/cop_thief/domain/strategy/qlearning_strategy.py), [`qlearning_trainer.py`](../src/cop_thief/domain/strategy/qlearning_trainer.py) |
| Config | [`config/rl.json`](../config/rl.json) → [`config/rl_config.py`](../src/cop_thief/config/rl_config.py) |
| CLI | `uv run cop-thief-train` |
| Version | 1.0.0 |

## 1. Purpose
Provide an *adaptive* Cop strategy that learns to capture, as the lecture
recommends. **Tabular** Q-Learning only — no neural networks (PRD §6).

## 2. Requirements
| ID | Requirement |
|----|-------------|
| Q-1 | State = joint `(cop, thief)` positions encoded to one integer; actions = 9 directions. |
| Q-2 | Bellman update `Q(s,a) ← Q(s,a) + α[r + γ·maxₐ′Q(s′,a′) − Q(s,a)]`. |
| Q-3 | ε-greedy exploration with decay; all of α, γ, ε, rewards are config-sourced and clamped. |
| Q-4 | Reward shaping: `+capture`, small `step` cost, `escape` penalty. |
| Q-5 | Q-table persists to / loads from JSON; only legal actions are chosen at play time. |

## 3. Design
- **`QTable`** — sparse `dict[state → list[9]]`, lazy rows, `best_value`,
  `greedy_index(allowed)`, `update(...)` (Bellman), `save`/`load`.
- **`encode_state(state, grid)`** — `cop_index · cells + thief_index`.
- **`QLearningTrainer`** — ε-greedy self-play: Cop learns vs the heuristic Thief;
  ε decays each episode; returns a trained table.
- **`QLearningStrategy`** — greedy play from a trained table over legal moves
  (drop-in Cop alternative to `HeuristicStrategy`).

## 4. Hyper-parameters (`config/rl.json`)
`alpha 0.2`, `gamma 0.9`, `epsilon 0.3 → epsilon_min 0.02` (`epsilon_decay 0.999`),
`reward_capture 20`, `reward_step −0.5`, `reward_escape −10`.

## 5. Acceptance criteria
- One terminal Bellman step moves the value to `α·reward` (`test_qlearning`).
- Encoding is unique per position pair; save/load round-trips.
- **Convergence:** a trained Cop captures ≥ 20/30 episodes vs the evader (`test_qlearning`).
