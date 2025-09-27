"""Configuration for the Plan service."""
from __future__ import annotations

from functools import lru_cache
from typing import Optional

from pydantic import AnyHttpUrl
from pydantic_settings import BaseSettings, SettingsConfigDict


class PlanSettings(BaseSettings):
    kernel_base_url: Optional[AnyHttpUrl] = None
    kernel_timeout: float = 30.0
    kernel_api_key: Optional[str] = None
    mongo_uri: Optional[str] = None
    mongo_db: str = "dyocense"
    mongo_collection: str = "plans"
    chat_collection: str = "plan_chats"

    model_config = SettingsConfigDict(env_prefix="PLAN_", env_file=".env", extra="allow")


@lru_cache()
def get_settings() -> PlanSettings:
    return PlanSettings()
