"""Leaf configuration sub-models: token economics, NL, reporting, network.

Split out of ``setup_models.py`` to keep every config module under the line
budget. All inherit the frozen, extra-tolerant :class:`FrozenModel`.
"""

from __future__ import annotations

from cop_thief.config.base_model import FrozenModel


class TokenRates(FrozenModel):
    """Per-million-token USD rates for the token-budget block."""

    input_per_million_usd: float
    output_per_million_usd: float


class ProviderRate(FrozenModel):
    """Per-provider USD pricing (per million input/output tokens)."""

    input: float
    output: float


class TokenBudget(FrozenModel):
    """Token economics and the hard cost ceiling."""

    version: str
    rates: TokenRates
    ceiling_usd: float
    warn_ratio: float = 0.80
    enforce_ceiling: bool = True
    usage_file: str = "data/token_usage.json"


class NlParserConfig(FrozenModel):
    """Defensive NL parser thresholds."""

    min_confidence: float = 0.60
    max_tokens: int = 200


class NlConfig(FrozenModel):
    """Natural-language subsystem configuration (encoder keys tolerated)."""

    parser: NlParserConfig = NlParserConfig()


class ReportingConfig(FrozenModel):
    """Reporting addresses and the production submission safety interlock."""

    examiner_email: str = "rmisegal+uoh26b@gmail.com"
    burner_email: str = "mcp.marl.telemetry@gmail.com"
    production_submission_locked: bool = True


class NetworkConfig(FrozenModel):
    """Two-team public URL matrix (ex06 §9.2): one Cop + one Thief per group."""

    team_alpha_cop_url: str = ""
    team_alpha_thief_url: str = ""
    team_beta_cop_url: str = ""
    team_beta_thief_url: str = ""
