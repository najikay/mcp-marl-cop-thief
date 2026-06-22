"""Strict, immutable Pydantic v2 models for ``config/setup.json``.

Split out of ``models.py`` to honour the 150-line-per-file limit (Guidelines
§3.2). All models are ``frozen=True`` for runtime immutability and
``extra="ignore"`` so descriptive ``comment`` keys in the JSON are tolerated.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class _Frozen(BaseModel):
    """Base config model: immutable and tolerant of descriptive extra keys."""

    model_config = ConfigDict(frozen=True, extra="ignore")


class GameConfig(_Frozen):
    """Immutable Dec-POMDP board parameters."""

    grid_size: list[int]
    max_moves: int
    num_games: int
    max_barriers: int
    allow_diagonal: bool = True
    start_mode: str = "random"
    random_seed: int | None = None
    thief_moves_first: bool = True


class ScoringConfig(_Frozen):
    """Immutable scoring matrix mapped from ex06 Table 1."""

    cop_win: int
    thief_win: int
    cop_loss: int
    thief_loss: int


class ServerConfig(_Frozen):
    """A single MCP server endpoint (cop or thief)."""

    mode: str
    url: str
    auth_env_var: str
    local_port: int | None = None


class LLMEndpoint(_Frozen):
    """One LLM provider endpoint in the dual-failover routing."""

    provider: str
    base_url: str
    model: str
    api_key_env_var: str
    timeout_seconds: int = 60


class LLMRouting(_Frozen):
    """Primary/fallback LLM routing."""

    primary: LLMEndpoint
    fallback: LLMEndpoint


class RewardConfig(_Frozen):
    """Reward-shaping values for the Q-Learning strategy."""

    r_capture: float
    r_evasion: float
    r_caught: float
    r_step: float
    r_invalid: float
    r_corner: float = -0.5


class RLConfig(_Frozen):
    """Tabular Q-Learning hyper-parameters."""

    enabled: bool = True
    alpha: float = 0.1
    gamma: float = 0.9
    epsilon_start: float = 1.0
    epsilon_min: float = 0.05
    epsilon_decay: float = 0.995
    rewards: RewardConfig


class TokenRates(_Frozen):
    """Per-million-token USD rates."""

    input_per_million_usd: float
    output_per_million_usd: float


class ProviderRate(_Frozen):
    """Per-provider USD pricing (per million input/output tokens)."""

    input: float
    output: float


class NlParserConfig(_Frozen):
    """Defensive NL parser thresholds."""

    min_confidence: float = 0.60
    max_tokens: int = 200


class NlConfig(_Frozen):
    """Natural-language subsystem configuration (encoder keys tolerated)."""

    parser: NlParserConfig = NlParserConfig()


class TokenBudget(_Frozen):
    """Token economics & hard cost ceiling."""

    version: str
    rates: TokenRates
    ceiling_usd: float
    warn_ratio: float = 0.80
    enforce_ceiling: bool = True
    usage_file: str = "data/token_usage.json"


class SetupConfig(_Frozen):
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
