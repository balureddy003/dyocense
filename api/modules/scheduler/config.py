"""Configuration for Scheduler service."""
from __future__ import annotations

from functools import lru_cache
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class SchedulerSettings(BaseSettings):
    mongo_uri: Optional[str] = None
    mongo_db: str = "dyocense"
    jobs_collection: str = "scheduler_jobs"
    tenants_collection: str = "scheduler_tenants"
    default_lease_seconds: int = 60

    model_config = SettingsConfigDict(env_prefix="SCHEDULER_", env_file=".env", extra="allow")


@lru_cache()
def get_settings() -> SchedulerSettings:
    return SchedulerSettings()
