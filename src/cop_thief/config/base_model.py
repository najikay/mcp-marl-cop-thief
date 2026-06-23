"""Shared frozen base for every configuration schema."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class FrozenModel(BaseModel):
    """Immutable config model that tolerates descriptive extra keys."""

    model_config = ConfigDict(frozen=True, extra="ignore")
