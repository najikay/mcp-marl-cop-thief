"""CLI: train the Cop Q-table by self-play and save it (excluded from coverage).

Usage::

    uv run cop-thief-train --episodes 20000 --out results/qtable.json
"""

from __future__ import annotations

import argparse

from .config import ConfigManager
from .config.rl_config import load_rl_config
from .domain.strategy import QLearningTrainer


def _parse_args() -> argparse.Namespace:  # pragma: no cover
    parser = argparse.ArgumentParser(description="Train the Cop Q-table.")
    parser.add_argument("--config", default=None)
    parser.add_argument("--rl-config", default=None)
    parser.add_argument("--episodes", type=int, default=20000)
    parser.add_argument("--out", default="results/qtable.json")
    return parser.parse_args()


def main() -> None:  # pragma: no cover
    """Train and persist the Q-table."""
    args = _parse_args()
    config = ConfigManager(args.config).load()
    rl = load_rl_config(args.rl_config)
    table = QLearningTrainer(config, rl).train(args.episodes)
    table.save(args.out)
    print(f"# trained {args.episodes} episodes -> {args.out}")


if __name__ == "__main__":
    main()
