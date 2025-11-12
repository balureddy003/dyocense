"""Migration script to create connector_data_chunks table and indexes.

Usage:
  python scripts/migrate_connector_data_chunks.py

Requires PostgresBackend active (PERSISTENCE_BACKEND=postgres).
"""
from __future__ import annotations

from packages.kernel_common.persistence_v2 import get_backend, PostgresBackend

DDL = """
CREATE TABLE IF NOT EXISTS connectors.connector_data_chunks (
  chunk_id TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
  tenant_id TEXT NOT NULL REFERENCES tenants.tenants(tenant_id) ON DELETE CASCADE,
  connector_id TEXT NOT NULL REFERENCES connectors.connectors(connector_id) ON DELETE CASCADE,
  data_type TEXT NOT NULL,
  chunk_index INT NOT NULL,
  data JSONB NOT NULL,
  record_count INT NOT NULL,
  synced_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  metadata JSONB DEFAULT '{}'
);

CREATE INDEX IF NOT EXISTS idx_connector_chunks_tenant ON connectors.connector_data_chunks (tenant_id, connector_id);
CREATE INDEX IF NOT EXISTS idx_connector_chunks_type ON connectors.connector_data_chunks (data_type);
CREATE INDEX IF NOT EXISTS idx_connector_chunks_synced ON connectors.connector_data_chunks (synced_at DESC);
"""

def main():
    backend = get_backend()
    if not isinstance(backend, PostgresBackend):
        print("Postgres backend not active; set PERSISTENCE_BACKEND=postgres")
        return
    with backend.get_connection() as conn:  # type: ignore[attr-defined]
        with conn.cursor() as cur:
            cur.execute(DDL)
        conn.commit()
    print("✅ connector_data_chunks table and indexes ensured")

if __name__ == "__main__":
    main()
