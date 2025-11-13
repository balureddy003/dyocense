"""
Background Jobs Package

Contains scheduled and background jobs for the Kernel service:
- daily_insights: Daily health score and recommendation generation (6am)
"""

from .daily_insights import (
    DailyInsightsJob,
    create_daily_insights_job,
    create_apscheduler_integration,
)

__all__ = [
    "DailyInsightsJob",
    "create_daily_insights_job",
    "create_apscheduler_integration",
]
