"""Repository for connector data persistence."""

import logging
from datetime import datetime
from typing import Optional
from pymongo import MongoClient
from pymongo.collection import Collection

from .models import TenantConnector, ConnectorStatus
from .encryption import get_encryption

logger = logging.getLogger(__name__)


class ConnectorRepository:
    """MongoDB repository for tenant connectors."""
    
    def __init__(self, mongo_client: MongoClient, database_name: str = "dyocense"):
        """
        Initialize the repository.
        
        Args:
            mongo_client: MongoDB client instance
            database_name: Name of the database
        """
        self.db = mongo_client[database_name]
        self.collection: Collection = self.db["tenant_connectors"]
        self.encryption = get_encryption()
        
        # Create indexes
        self._ensure_indexes()
    
    def _ensure_indexes(self):
        """Ensure required indexes exist."""
        try:
            # Tenant ID index for fast lookup
            self.collection.create_index("tenant_id")
            # Connector ID index (unique)
            self.collection.create_index("connector_id", unique=True)
            # Compound index for tenant + status
            self.collection.create_index([("tenant_id", 1), ("status", 1)])
        except Exception as e:
            logger.warning(f"Failed to create indexes: {e}")
    
    def create(
        self,
        tenant_id: str,
        connector_type: str,
        connector_name: str,
        display_name: str,
        category: str,
        icon: str,
        config: dict,
        data_types: list[str],
        created_by: str,
        sync_frequency: str = "manual",
    ) -> TenantConnector:
        """
        Create a new connector configuration.
        
        Args:
            tenant_id: Tenant ID
            connector_type: Type of connector (e.g., "xero", "google-drive")
            connector_name: Internal name
            display_name: User-friendly name
            category: Category
            icon: Icon name
            config: Configuration dict (will be encrypted)
            data_types: List of data types
            created_by: User ID
            sync_frequency: Sync frequency
            
        Returns:
            Created TenantConnector
        """
        import secrets
        
        connector_id = f"conn-{secrets.token_urlsafe(16)}"
        encrypted_config = self.encryption.encrypt_config(config)
        
        connector = TenantConnector(
            connector_id=connector_id,
            tenant_id=tenant_id,
            connector_type=connector_type,
            connector_name=connector_name,
            display_name=display_name,
            category=category,
            icon=icon,
            encrypted_config=encrypted_config,
            data_types=data_types,
            status=ConnectorStatus.TESTING,
            sync_frequency=sync_frequency,  # type: ignore
            created_by=created_by,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        
        self.collection.insert_one(connector.model_dump())
        logger.info(f"Created connector {connector_id} for tenant {tenant_id}")
        
        return connector
    
    def get_by_id(self, connector_id: str) -> Optional[TenantConnector]:
        """Get a connector by ID."""
        doc = self.collection.find_one({"connector_id": connector_id})
        if not doc:
            return None
        return TenantConnector(**doc)
    
    def list_by_tenant(
        self,
        tenant_id: str,
        status: Optional[ConnectorStatus] = None
    ) -> list[TenantConnector]:
        """
        List all connectors for a tenant.
        
        Args:
            tenant_id: Tenant ID
            status: Optional status filter
            
        Returns:
            List of connectors
        """
        query = {"tenant_id": tenant_id}
        if status:
            query["status"] = status.value
        
        docs = self.collection.find(query).sort("created_at", -1)
        return [TenantConnector(**doc) for doc in docs]
    
    def update_status(
        self,
        connector_id: str,
        status: ConnectorStatus,
        error_message: Optional[str] = None
    ) -> bool:
        """
        Update connector status.
        
        Args:
            connector_id: Connector ID
            status: New status
            error_message: Optional error message if status is ERROR
            
        Returns:
            True if updated, False if not found
        """
        update_data = {
            "status": status.value,
            "updated_at": datetime.utcnow(),
        }
        
        if error_message:
            update_data["metadata.error_message"] = error_message
            update_data["metadata.last_error_at"] = datetime.utcnow()
        
        result = self.collection.update_one(
            {"connector_id": connector_id},
            {"$set": update_data}
        )
        
        return result.modified_count > 0
    
    def update_sync_info(
        self,
        connector_id: str,
        total_records: int,
        duration: float
    ) -> bool:
        """
        Update sync metadata after successful sync.
        
        Args:
            connector_id: Connector ID
            total_records: Number of records synced
            duration: Sync duration in seconds
            
        Returns:
            True if updated, False if not found
        """
        result = self.collection.update_one(
            {"connector_id": connector_id},
            {
                "$set": {
                    "last_sync": datetime.utcnow(),
                    "status": ConnectorStatus.ACTIVE.value,
                    "metadata.total_records": total_records,
                    "metadata.last_sync_duration": duration,
                    "metadata.error_message": None,
                    "updated_at": datetime.utcnow(),
                }
            }
        )
        
        return result.modified_count > 0
    
    def delete(self, connector_id: str, tenant_id: str) -> bool:
        """
        Delete a connector (with tenant verification).
        
        Args:
            connector_id: Connector ID
            tenant_id: Tenant ID (for security verification)
            
        Returns:
            True if deleted, False if not found
        """
        result = self.collection.delete_one({
            "connector_id": connector_id,
            "tenant_id": tenant_id
        })
        
        if result.deleted_count > 0:
            logger.info(f"Deleted connector {connector_id}")
            return True
        return False
    
    def get_decrypted_config(self, connector_id: str) -> Optional[dict]:
        """
        Get decrypted configuration for a connector.
        
        WARNING: Only use this internally. Never expose decrypted config via API.
        
        Args:
            connector_id: Connector ID
            
        Returns:
            Decrypted configuration dict or None if not found
        """
        connector = self.get_by_id(connector_id)
        if not connector:
            return None
        
        try:
            return self.encryption.decrypt_config(connector.encrypted_config)
        except Exception as e:
            logger.error(f"Failed to decrypt config for {connector_id}: {e}")
            return None
