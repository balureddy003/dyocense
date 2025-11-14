"""
Base Connector Interface

Abstract base class for all data source connectors.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, AsyncIterator
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class SyncStatus:
    """Sync status constants."""
    SUCCESS = "success"
    PARTIAL = "partial"
    FAILED = "failed"
    IN_PROGRESS = "in_progress"


class ConnectorBase(ABC):
    """
    Abstract base class for data connectors.
    
    All connectors must implement:
    - authenticate(): Validate credentials
    - sync(): Pull data from source
    - validate_config(): Validate configuration
    """
    
    def __init__(
        self,
        source_id: UUID,
        tenant_id: UUID,
        credentials: dict[str, Any],
        config: dict[str, Any],
        db: AsyncSession
    ):
        """
        Initialize connector.
        
        Args:
            source_id: DataSource ID
            tenant_id: Tenant ID
            credentials: Authentication credentials
            config: Connector configuration
            db: Database session
        """
        self.source_id = source_id
        self.tenant_id = tenant_id
        self.credentials = credentials
        self.config = config
        self.db = db
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    @abstractmethod
    async def authenticate(self) -> bool:
        """
        Test authentication with data source.
        
        Returns:
            True if authentication successful
        
        Raises:
            AuthenticationError if credentials invalid
        """
        pass
    
    @abstractmethod
    async def sync(self) -> dict[str, Any]:
        """
        Sync data from source to database.
        
        Returns:
            Sync result with statistics (records_synced, errors, duration, etc.)
        """
        pass
    
    @abstractmethod
    async def validate_config(self) -> tuple[bool, str]:
        """
        Validate connector configuration.
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        pass
    
    async def get_sync_status(self) -> dict[str, Any]:
        """Get current sync status from database."""
        from backend.models import DataSource
        from sqlalchemy import select
        
        result = await self.db.execute(
            select(DataSource).where(DataSource.source_id == self.source_id)
        )
        source = result.scalar_one_or_none()
        
        if not source:
            return {"status": "not_found"}
        
        return {
            "status": source.status,
            "last_sync": source.last_sync,
            "config": source.config
        }
    
    async def update_sync_status(
        self,
        status: str,
        last_sync: datetime | None = None,
        error_message: str | None = None
    ) -> None:
        """Update sync status in database."""
        from backend.models import DataSource
        from sqlalchemy import select
        
        result = await self.db.execute(
            select(DataSource).where(DataSource.source_id == self.source_id)
        )
        source = result.scalar_one_or_none()
        
        if source:
            source.status = status
            if last_sync:
                source.last_sync = last_sync
            if error_message:
                if not source.extra_data:
                    source.extra_data = {}
                source.extra_data["last_error"] = error_message
            
            await self.db.commit()
    
    async def save_metrics(self, metrics: list[dict[str, Any]]) -> int:
        """
        Save business metrics to database.
        
        Args:
            metrics: List of metric dicts with keys:
                - metric_name: str
                - value: float
                - timestamp: datetime
                - metric_type: str (optional)
                - unit: str (optional)
        
        Returns:
            Number of metrics saved
        """
        from backend.models import BusinessMetric
        
        saved = 0
        for metric_data in metrics:
            metric = BusinessMetric(
                tenant_id=self.tenant_id,
                metric_name=metric_data["metric_name"],
                value=metric_data["value"],
                timestamp=metric_data.get("timestamp", datetime.utcnow()),
                metric_type=metric_data.get("metric_type"),
                unit=metric_data.get("unit"),
                source=self.__class__.__name__,
                extra_data=metric_data.get("metadata", {})
            )
            self.db.add(metric)
            saved += 1
        
        await self.db.commit()
        self.logger.info(f"Saved {saved} metrics to database")
        
        return saved


class ConnectorError(Exception):
    """Base exception for connector errors."""
    pass


class AuthenticationError(ConnectorError):
    """Authentication failed."""
    pass


class SyncError(ConnectorError):
    """Sync operation failed."""
    pass


class ConfigurationError(ConnectorError):
    """Configuration invalid."""
    pass
