"""Core Pydantic v2 models for ``config/setup.json`` and the root ``SetupConfig``.

Leaf sub-models (token economics, NL, reporting, network) live in
``aux_models.py``; the shared frozen base lives in ``base_model.py``.
"""

from __future__ import annotations

from cop_thief.config.aux_models import (
    GroupConfig,
    NetworkConfig,
    NlConfig,
    ProviderRate,
    ReportingConfig,
    TokenBudget,
)
from cop_thief.config.base_model import FrozenModel


class GameConfig(FrozenModel):
    """Immutable Dec-POMDP board parameters."""

    grid_size: list[int]
    max_moves: int
    num_games: int
    max_barriers: int
    allow_diagonal: bool = True
    start_mode: str = "random"
    random_seed: int | None = None
    thief_moves_first: bool = True
    deterministic_moves: bool = True  # tournament: move = pure fn(observation) → byte-agreeing replays
    barriers_enabled: bool = True     # per-match agreement (some opponents negotiate barriers OFF)
    fixed_start: dict | None = None   # {"cop": [r,c], "thief": [r,c]} when start_mode == "fixed"


class ScoringConfig(FrozenModel):
    """Immutable scoring matrix mapped from ex06 Table 1."""

    cop_win: int
    thief_win: int
    cop_loss: int
    thief_loss: int


class ServerConfig(FrozenModel):
    """A single MCP server endpoint (cop or thief)."""

    mode: str
    url: str
    auth_env_var: str
    local_port: int | None = None


class LLMEndpoint(FrozenModel):
    """One LLM provider endpoint in the dual-failover routing."""

    provider: str
    base_url: str
    model: str
    api_key_env_var: str
    timeout_seconds: int = 60


class LLMRouting(FrozenModel):
    """Primary/fallback LLM routing."""

    primary: LLMEndpoint
    fallback: LLMEndpoint


class RewardConfig(FrozenModel):
    """Reward-shaping values for the Q-Learning strategy."""

    r_capture: float
    r_evasion: float
    r_caught: float
    r_step: float
    r_invalid: float
    r_corner: float = -0.5


class RLConfig(FrozenModel):
    """Tabular Q-Learning hyper-parameters."""

    enabled: bool = True
    alpha: float = 0.1
    gamma: float = 0.9
    epsilon_start: float = 1.0
    epsilon_min: float = 0.05
    epsilon_decay: float = 0.995
    q_confidence_margin: float = 0.05
    rewards: RewardConfig


class SetupConfig(FrozenModel):
    """Root schema for ``config/setup.json`` (immutable game parameters)."""

    version: str
    game: GameConfig
    scoring: ScoringConfig
    servers: dict[str, ServerConfig]
    llm_routing: LLMRouting
    rl: RLConfig
    token_budget: TokenBudget
    economics: dict[str, ProviderRate]
    nl: NlConfig = NlConfig()
    reporting: ReportingConfig = ReportingConfig()
    network: NetworkConfig = NetworkConfig()
    group: GroupConfig = GroupConfig()
    opponent: GroupConfig = GroupConfig()
