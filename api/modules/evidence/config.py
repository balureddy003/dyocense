"""Configuration for the Evidence service."""
from __future__ import annotations

from functools import lru_cache
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class EvidenceSettings(BaseSettings):
    mongo_uri: Optional[str] = None
    mongo_db: str = "dyocense"
    evidence_collection: str = "evidence_snapshots"

    model_config = SettingsConfigDict(env_prefix="EVIDENCE_", env_file=".env", extra="allow")


@lru_cache()
def get_settings() -> EvidenceSettings:
    return EvidenceSettings()
