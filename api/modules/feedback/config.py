"""Configuration for Feedback service."""
from __future__ import annotations

from functools import lru_cache
from typing import Optional

from pydantic import AnyHttpUrl
from pydantic_settings import BaseSettings, SettingsConfigDict


class FeedbackSettings(BaseSettings):
    mongo_uri: Optional[str] = None
    mongo_db: str = "dyocense"
    collection: str = "feedback_events"
    kernel_base_url: Optional[AnyHttpUrl] = None
    kernel_timeout: float = 30.0
    kernel_api_key: Optional[str] = None
    scheduler_url: Optional[AnyHttpUrl] = None
    scheduler_timeout: float = 10.0

    model_config = SettingsConfigDict(env_prefix="FEEDBACK_", env_file=".env", extra="allow")


@lru_cache()
def get_settings() -> FeedbackSettings:
    return FeedbackSettings()
