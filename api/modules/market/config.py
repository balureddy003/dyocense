"""Configuration for Market service."""
from __future__ import annotations

from functools import lru_cache
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class MarketSettings(BaseSettings):
    mongo_uri: Optional[str] = None
    mongo_db: str = "dyocense"
    collection: str = "market_intel"

    model_config = SettingsConfigDict(env_prefix="MARKET_", env_file=".env", extra="allow")


@lru_cache()
def get_settings() -> MarketSettings:
    return MarketSettings()
