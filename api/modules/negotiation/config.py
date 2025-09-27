"""Configuration for Negotiation service."""
from __future__ import annotations

from functools import lru_cache
from typing import Optional

from pydantic import AnyHttpUrl
from pydantic_settings import BaseSettings, SettingsConfigDict


class NegotiationSettings(BaseSettings):
    plan_service_url: Optional[AnyHttpUrl] = None
    plan_timeout: float = 10.0

    model_config = SettingsConfigDict(env_prefix="NEGOTIATION_", env_file=".env", extra="allow")


@lru_cache()
def get_settings() -> NegotiationSettings:
    return NegotiationSettings()
