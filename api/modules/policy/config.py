"""Configuration for Policy service."""
from __future__ import annotations

from functools import lru_cache
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class PolicySettings(BaseSettings):
    mongo_uri: Optional[str] = None
    mongo_db: str = "dyocense"
    policies_collection: str = "policies"
    audits_collection: str = "policy_audits"

    model_config = SettingsConfigDict(env_prefix="POLICY_", env_file=".env", extra="allow")


@lru_cache()
def get_settings() -> PolicySettings:
    return PolicySettings()
