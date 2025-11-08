"""PostgreSQL repository for connector data persistence (SMB unified backend).

Mirrors the Mongo-based ConnectorRepository API while leveraging the consolidated
Postgres schema (`connectors.connectors` table). This avoids redundant databases
while retaining strong encryption + flexible metadata via JSONB.
"""
from __future__ import annotations

import logging
import os
from datetime import datetime
from typing import Optional, Any

from packages.kernel_common.persistence_v2 import get_backend, PostgresBackend
from .models import TenantConnector, ConnectorStatus, ConnectorMetadata, SyncFrequency
from .encryption import get_encryption

logger = logging.getLogger(__name__)


class ConnectorRepositoryPG:
    """PostgreSQL repository for tenant connectors.

    Table expectation (extended vs initial schema):
        connector_id TEXT PK
        tenant_id TEXT
        connector_type TEXT
        connector_name TEXT
        display_name TEXT
        category TEXT
        icon TEXT
        data_types TEXT[]
        sync_frequency TEXT
        created_by TEXT
        config_encrypted BYTEA
        encryption_key_id TEXT NULL
        status TEXT
        last_sync TIMESTAMPTZ
        metadata JSONB
        created_at TIMESTAMPTZ
        updated_at TIMESTAMPTZ
    """

    def __init__(self):
        backend = get_backend()
        if not isinstance(backend, PostgresBackend):
            raise RuntimeError("ConnectorRepositoryPG requires PostgresBackend")
        self._backend: PostgresBackend = backend
        self.encryption = get_encryption()

    # ------------------------------------------------------------------
    # Creation
    # ------------------------------------------------------------------
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
        import secrets
        connector_id = f"conn-{secrets.token_urlsafe(16)}"
        encrypted_config = self.encryption.encrypt_config(config)

        metadata = ConnectorMetadata()

        insert_sql = """
            INSERT INTO connectors.connectors (
              connector_id, tenant_id, connector_type, connector_name, display_name,
              category, icon, data_types, sync_frequency, created_by,
              config_encrypted, status, metadata, created_at, updated_at
            ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,NOW(),NOW())
            RETURNING created_at, updated_at
        """
        params = [
            connector_id, tenant_id, connector_type, connector_name, display_name,
            category, icon, data_types, sync_frequency, created_by,
            encrypted_config.encode(), ConnectorStatus.TESTING.value, metadata.model_dump_json(),
        ]

        with self._backend.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(insert_sql, params)
                row = cur.fetchone()

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
            sync_frequency=SyncFrequency(sync_frequency),
            metadata=metadata,
            created_at=row[0] if row else datetime.utcnow(),
            updated_at=row[1] if row else datetime.utcnow(),
            created_by=created_by,
        )
        logger.info(f"Created connector {connector_id} (tenant={tenant_id}) in Postgres")
        return connector

    # ------------------------------------------------------------------
    # Retrieval helpers
    # ------------------------------------------------------------------
    def _row_to_model(self, row: Any) -> TenantConnector:
        metadata_dict = row.get("metadata") if isinstance(row, dict) else row[-3]
        # If using RealDictCursor we'll have dict access; otherwise index positions vary.
        if isinstance(row, dict):
            encrypted_bytes = row.get("config_encrypted") or b""
            encrypted_config = encrypted_bytes.decode() if isinstance(encrypted_bytes, (bytes, bytearray)) else str(encrypted_bytes)
            metadata_raw = metadata_dict if isinstance(metadata_dict, dict) else {}
            meta = ConnectorMetadata(**metadata_raw) if isinstance(metadata_raw, dict) else ConnectorMetadata()
            return TenantConnector(
                connector_id=row["connector_id"],
                tenant_id=row["tenant_id"],
                connector_type=row["connector_type"],
                connector_name=row.get("connector_name", row["connector_type"]),
                display_name=row["display_name"],
                category=row.get("category", "uncategorised"),
                icon=row.get("icon", "Plug"),
                encrypted_config=encrypted_config,
                data_types=row.get("data_types", []),
                status=ConnectorStatus(row.get("status", ConnectorStatus.TESTING.value)),
                last_sync=row.get("last_sync"),
                sync_frequency=SyncFrequency(row.get("sync_frequency", "manual")),
                metadata=meta,
                created_at=row.get("created_at", datetime.utcnow()),
                updated_at=row.get("updated_at", datetime.utcnow()),
                created_by=row.get("created_by", "system"),
            )
        # Fallback simplistic mapping (should not normally hit)
        return TenantConnector(
            connector_id=row[0], tenant_id=row[1], connector_type=row[2], connector_name=row[2],
            display_name=row[3], category="uncategorised", icon="Plug", encrypted_config="",
            data_types=[], status=ConnectorStatus.TESTING, sync_frequency=SyncFrequency.MANUAL,
            metadata=ConnectorMetadata(), created_at=datetime.utcnow(), updated_at=datetime.utcnow(), created_by="system"
        )

    def get_by_id(self, connector_id: str) -> Optional[TenantConnector]:
        sql = "SELECT * FROM connectors.connectors WHERE connector_id=%s"
        with self._backend.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, [connector_id])
                colnames = [desc[0] for desc in cur.description] if cur.description else []
                row = cur.fetchone()
                if not row:
                    return None
                if colnames:
                    row_dict = dict(zip(colnames, row))
                    return self._row_to_model(row_dict)
                return self._row_to_model(row)

    def list_by_tenant(self, tenant_id: str, status: Optional[ConnectorStatus] = None) -> list[TenantConnector]:
        sql = "SELECT * FROM connectors.connectors WHERE tenant_id=%s"
        params: list[Any] = [tenant_id]
        if status:
            sql += " AND status=%s"
            params.append(status.value)
        sql += " ORDER BY created_at DESC"
        results: list[TenantConnector] = []
        with self._backend.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, params)
                colnames = [desc[0] for desc in cur.description] if cur.description else []
                for row in cur.fetchall():
                    row_dict = dict(zip(colnames, row)) if colnames else row
                    results.append(self._row_to_model(row_dict))
        return results

    # ------------------------------------------------------------------
    # Updates
    # ------------------------------------------------------------------
    def update_status(self, connector_id: str, status: ConnectorStatus, error_message: Optional[str] = None) -> bool:
        # Fetch current metadata
        connector = self.get_by_id(connector_id)
        if not connector:
            return False
        meta = connector.metadata
        if error_message:
            meta.error_message = error_message
            meta.last_error_at = datetime.utcnow()
        update_sql = """
            UPDATE connectors.connectors
            SET status=%s, metadata=%s, updated_at=NOW()
            WHERE connector_id=%s
        """
        with self._backend.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(update_sql, [status.value, meta.model_dump_json(), connector_id])
                return cur.rowcount > 0

    def update_sync_info(self, connector_id: str, total_records: int, duration: float) -> bool:
        connector = self.get_by_id(connector_id)
        if not connector:
            return False
        meta = connector.metadata
        meta.total_records = total_records
        meta.last_sync_duration = duration
        update_sql = """
            UPDATE connectors.connectors
            SET last_sync=NOW(), status=%s, metadata=%s, updated_at=NOW()
            WHERE connector_id=%s
        """
        with self._backend.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(update_sql, [ConnectorStatus.ACTIVE.value, meta.model_dump_json(), connector_id])
                return cur.rowcount > 0

    # ------------------------------------------------------------------
    # Delete
    # ------------------------------------------------------------------
    def delete(self, connector_id: str, tenant_id: str) -> bool:
        sql = "DELETE FROM connectors.connectors WHERE connector_id=%s AND tenant_id=%s"
        with self._backend.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, [connector_id, tenant_id])
                deleted = cur.rowcount > 0
        if deleted:
            logger.info(f"Deleted connector {connector_id} (tenant={tenant_id}) from Postgres")
        return deleted

    # ------------------------------------------------------------------
    # Secure config access
    # ------------------------------------------------------------------
    def get_decrypted_config(self, connector_id: str) -> Optional[dict]:
        connector = self.get_by_id(connector_id)
        if not connector:
            return None
        try:
            return self.encryption.decrypt_config(connector.encrypted_config)
        except Exception as e:
            logger.error(f"Failed to decrypt config for {connector_id}: {e}")
            return None

__all__ = ["ConnectorRepositoryPG"]
