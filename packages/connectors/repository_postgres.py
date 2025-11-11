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
        self._ensure_schema()

    def _ensure_schema(self):
        """Ensure required columns exist in connectors table."""
        try:
            print("🔍 Checking connectors.connectors schema...")
            with self._backend.get_connection() as conn:
                with conn.cursor() as cur:
                    # Check if connector_name column exists
                    cur.execute("""
                        SELECT column_name 
                        FROM information_schema.columns 
                        WHERE table_schema = 'connectors' 
                        AND table_name = 'connectors' 
                        AND column_name = 'connector_name'
                    """)
                    
                    result = cur.fetchone()
                    if not result:
                        print("⚠️ Missing columns detected. Starting migration...")
                        logger.info("Adding missing columns to connectors.connectors table...")
                        
                        # Add missing columns with defaults
                        cur.execute("""
                            ALTER TABLE connectors.connectors 
                            ADD COLUMN IF NOT EXISTS connector_name TEXT NOT NULL DEFAULT '',
                            ADD COLUMN IF NOT EXISTS display_name TEXT NOT NULL DEFAULT '',
                            ADD COLUMN IF NOT EXISTS category TEXT,
                            ADD COLUMN IF NOT EXISTS icon TEXT,
                            ADD COLUMN IF NOT EXISTS data_types TEXT[] DEFAULT ARRAY[]::TEXT[],
                            ADD COLUMN IF NOT EXISTS sync_frequency TEXT DEFAULT 'manual',
                            ADD COLUMN IF NOT EXISTS created_by TEXT,
                            ADD COLUMN IF NOT EXISTS sync_status TEXT,
                            ADD COLUMN IF NOT EXISTS sync_error TEXT,
                            ADD COLUMN IF NOT EXISTS metadata JSONB DEFAULT '{}'
                        """)
                        print("✅ Columns added")
                        
                        # Update existing rows
                        cur.execute("""
                            UPDATE connectors.connectors 
                            SET connector_name = connector_type,
                                display_name = connector_type,
                                sync_frequency = COALESCE(sync_frequency, 'manual')
                            WHERE connector_name = '' OR display_name = ''
                        """)
                        print("✅ Existing rows updated")
                        
                        conn.commit()
                        print("✅ Schema migration completed successfully")
                        logger.info("✅ Schema migration completed successfully")
                    else:
                        print("✅ Schema is up to date")
                    
        except Exception as e:
            print(f"❌ Schema migration failed: {e}")
            logger.warning(f"Schema check/migration failed (non-fatal): {e}")
            import traceback
            traceback.print_exc()
            # Don't fail startup if schema migration fails

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
            encrypted_config.encode(), ConnectorStatus.INACTIVE.value, metadata.model_dump_json(),
        ]

        with self._backend.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(insert_sql, params)
                row = cur.fetchone()
            conn.commit()

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
            status=ConnectorStatus.INACTIVE,
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
            if isinstance(encrypted_bytes, memoryview):
                encrypted_bytes = encrypted_bytes.tobytes()
            if isinstance(encrypted_bytes, (bytes, bytearray)):
                encrypted_config = encrypted_bytes.decode()
            else:
                encrypted_config = str(encrypted_bytes)
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
        
        logger.info(f"Querying connectors: tenant_id={tenant_id}, status={status}, sql={sql}")
        
        results: list[TenantConnector] = []
        with self._backend.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, params)
                colnames = [desc[0] for desc in cur.description] if cur.description else []
                rows = cur.fetchall()
                logger.info(f"Query returned {len(rows)} rows")
                for row in rows:
                    row_dict = dict(zip(colnames, row)) if colnames else row
                    results.append(self._row_to_model(row_dict))
        
        logger.info(f"Converted to {len(results)} TenantConnector models")
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
                updated = cur.rowcount > 0
            if updated:
                conn.commit()
            return updated

    def update_metadata_flag(self, connector_id: str, **flags) -> bool:
        """Update JSONB metadata flags (e.g., mcp_enabled)."""
        connector = self.get_by_id(connector_id)
        if not connector:
            return False
        # Merge flags into existing metadata
        meta = connector.metadata.model_dump()
        meta.update(flags)
        sql = "UPDATE connectors.connectors SET metadata=%s, updated_at=NOW() WHERE connector_id=%s"
        with self._backend.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, [ConnectorMetadata(**meta).model_dump_json(), connector_id])
            conn.commit()
        return True

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
                updated = cur.rowcount > 0
            if updated:
                conn.commit()
            return updated

    # ------------------------------------------------------------------
    # Delete
    # ------------------------------------------------------------------
    def delete(self, connector_id: str, tenant_id: str) -> bool:
        sql = "DELETE FROM connectors.connectors WHERE connector_id=%s AND tenant_id=%s"
        with self._backend.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, [connector_id, tenant_id])
                deleted = cur.rowcount > 0
            conn.commit()
        if deleted:
            logger.info(f"Deleted connector {connector_id} (tenant={tenant_id}) from Postgres")
        return deleted

    def update(
        self,
        connector_id: str,
        tenant_id: str,
        *,
        display_name: Optional[str] = None,
        config: Optional[dict] = None,
        sync_frequency: Optional[str] = None,
        status: Optional[ConnectorStatus] = None,
        metadata: Optional[ConnectorMetadata] = None,
    ) -> Optional[TenantConnector]:
        """
        Update connector properties and re-encrypt configuration if provided.
        """
        existing = self.get_by_id(connector_id)
        if not existing or existing.tenant_id != tenant_id:
            return None

        new_display_name = display_name or existing.display_name
        new_sync_frequency = sync_frequency or existing.sync_frequency.value
        new_status = status or existing.status
        new_metadata = metadata or existing.metadata

        if config is not None:
            encrypted_config = self.encryption.encrypt_config(config)
        else:
            encrypted_config = existing.encrypted_config

        update_sql = """
            UPDATE connectors.connectors
               SET display_name=%s,
                   sync_frequency=%s,
                   config_encrypted=%s,
                   status=%s,
                   metadata=%s,
                   updated_at=NOW()
             WHERE connector_id=%s AND tenant_id=%s
        """

        params = [
            new_display_name,
            new_sync_frequency,
            encrypted_config.encode() if isinstance(encrypted_config, str) else encrypted_config,
            new_status.value,
            new_metadata.model_dump_json(),
            connector_id,
            tenant_id,
        ]

        with self._backend.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(update_sql, params)
            conn.commit()

        logger.info(f"Updated connector {connector_id} (tenant={tenant_id}) in Postgres")
        return self.get_by_id(connector_id)

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
