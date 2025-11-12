"""PostgreSQL data store helpers for scalable connector data ingestion.

Provides chunked append ingestion and unified retrieval across legacy
`connector_data` table and new `connector_data_chunks` table.
"""
from __future__ import annotations

from typing import Any, Iterable, Dict, List, Tuple

import math

from packages.kernel_common.logging import configure_logging, log_flow_event
from packages.kernel_common.persistence_v2 import get_backend, PostgresBackend

logger = configure_logging("connectors-data-store")

DEFAULT_CHUNK_SIZE = 5000  # tune based on average record size / RU costs

class ConnectorDataStore:
    def __init__(self):
        backend = get_backend()
        if not isinstance(backend, PostgresBackend):
            raise RuntimeError("ConnectorDataStore requires PostgresBackend")
        self.backend: PostgresBackend = backend

    # --------------------------------------------------------------
    # Ingestion
    # --------------------------------------------------------------
    def upsert_compact(self, tenant_id: str, connector_id: str, data_type: str, records: List[Dict[str, Any]], metadata: Dict[str, Any] | None = None) -> Dict[str, Any]:
        """Legacy single-row upsert (kept for small datasets)."""
        from psycopg2.extras import Json
        logger.info(f"[upsert_compact] STARTING: tenant={tenant_id}, connector={connector_id}, type={data_type}, records={len(records)}")
        logger.info(f"[upsert_compact] First record sample: {records[0] if records else 'EMPTY'}")
        log_flow_event(
            logger,
            stage="db_write",
            source="service",
            target="postgres",
            message="Starting compact upsert",
            metadata={
                "tenant_id": tenant_id,
                "connector_id": connector_id,
                "data_type": data_type,
                "records": len(records),
            },
        )
        
        with self.backend.get_connection() as conn:  # type: ignore[attr-defined]
            with conn.cursor() as cur:
                logger.debug(f"[upsert_compact] Executing INSERT for tenant={tenant_id}, connector={connector_id}, type={data_type}")
                cur.execute(
                    """
                    INSERT INTO connectors.connector_data
                    (tenant_id, connector_id, data_type, data, record_count, synced_at, metadata)
                    VALUES (%s, %s, %s, %s, %s, NOW(), %s)
                    ON CONFLICT (tenant_id, connector_id, data_type)
                    DO UPDATE SET
                      data = EXCLUDED.data,
                      record_count = EXCLUDED.record_count,
                      synced_at = NOW(),
                      metadata = EXCLUDED.metadata
                    RETURNING data_id, synced_at
                    """,
                    (
                        tenant_id,
                        connector_id,
                        data_type,
                        Json(records),
                        len(records),
                        Json(metadata or {}),
                    ),
                )
                row = cur.fetchone()
                logger.info(f"[upsert_compact] INSERT returned: data_id={row[0]}, synced_at={row[1]}")
            conn.commit()
            logger.info(f"[upsert_compact] COMMITTED: {len(records)} records for {tenant_id}/{connector_id}/{data_type}")
        
        result = {"mode": "compact", "data_id": row[0], "synced_at": row[1], "record_count": len(records)}
        logger.info(f"[upsert_compact] SUCCESS: {result}")
        return result

    def append_chunked(self, tenant_id: str, connector_id: str, data_type: str, records: List[Dict[str, Any]], metadata: Dict[str, Any] | None = None, chunk_size: int = DEFAULT_CHUNK_SIZE) -> Dict[str, Any]:
        """Append records as multiple chunk rows.

        Does NOT delete/replace previous data; retains historical batches.
        For cost control you can later prune older chunks.
        """
        if not records:
            return {"mode": "chunked", "chunks": 0, "record_count": 0}
        from psycopg2.extras import Json
        total = len(records)
        chunks = math.ceil(total / chunk_size)
        log_flow_event(
            logger,
            stage="db_write",
            source="service",
            target="postgres",
            message="Persisting data in chunked mode",
            metadata={
                "tenant_id": tenant_id,
                "connector_id": connector_id,
                "data_type": data_type,
                "records": total,
                "chunks": chunks,
            },
        )
        with self.backend.get_connection() as conn:  # type: ignore[attr-defined]
            try:
                with conn.cursor() as cur:
                    for i in range(chunks):
                        start = i * chunk_size
                        end = min(start + chunk_size, total)
                        slice_records = records[start:end]
                        cur.execute(
                            """
                            INSERT INTO connectors.connector_data_chunks
                            (tenant_id, connector_id, data_type, chunk_index, data, record_count, synced_at, metadata)
                            VALUES (%s, %s, %s, %s, %s, %s, NOW(), %s)
                            """,
                            (
                                tenant_id,
                                connector_id,
                                data_type,
                                i,
                                Json(slice_records),
                                len(slice_records),
                                Json(metadata or {}),
                            ),
                        )
                    conn.commit()
            except Exception as e:
                logger.warning("Chunked ingestion failed (likely table missing): %s. Falling back to compact upsert.", e)
                log_flow_event(
                    logger,
                    stage="db_write",
                    source="service",
                    target="postgres",
                    message="Chunked ingestion failed; reverting to compact upsert",
                    metadata={"error": str(e)},
                    level="WARNING",
                )
                # Fallback to compact to avoid ingestion failure
                return self.upsert_compact(tenant_id, connector_id, data_type, records, metadata)
        logger.info("Appended %s chunks (%s records) for %s/%s/%s", chunks, total, tenant_id, connector_id, data_type)
        return {"mode": "chunked", "chunks": chunks, "record_count": total}

    def ingest(self, tenant_id: str, connector_id: str, data_type: str, records: List[Dict[str, Any]], metadata: Dict[str, Any] | None = None) -> Dict[str, Any]:
        """Smart ingestion: compact for small sets, chunked for large sets."""
        threshold = DEFAULT_CHUNK_SIZE
        if len(records) <= threshold:
            log_flow_event(
                logger,
                stage="db_write",
                source="service",
                target="postgres",
                message="Switching to compact ingestion (below threshold)",
                metadata={
                    "tenant_id": tenant_id,
                    "connector_id": connector_id,
                    "data_type": data_type,
                    "records": len(records),
                },
            )
            return self.upsert_compact(tenant_id, connector_id, data_type, records, metadata)
        log_flow_event(
            logger,
            stage="db_write",
            source="service",
            target="postgres",
            message="Chunked ingestion chosen (above threshold)",
            metadata={
                "tenant_id": tenant_id,
                "connector_id": connector_id,
                "data_type": data_type,
                "records": len(records),
                "chunk_size": threshold,
            },
        )
        return self.append_chunked(tenant_id, connector_id, data_type, records, metadata)

    # --------------------------------------------------------------
    # Retrieval
    # --------------------------------------------------------------
    def fetch_all(self, tenant_id: str, connector_ids: List[str] | None = None, data_types: List[str] | None = None, limit_per_type: int | None = None) -> Dict[str, List[Dict[str, Any]]]:
        """Unified retrieval merging compact and chunked storage.

        limit_per_type: if set, truncates aggregated list per data_type to given number of records (recent first).
        """
        filters = []
        params: List[Any] = [tenant_id]
        if connector_ids:
            filters.append("connector_id = ANY(%s)")
            params.append(connector_ids)
        if data_types:
            filters.append("data_type = ANY(%s)")
            params.append(data_types)
        where = " AND ".join(filters)
        if where:
            where = " AND " + where
        result: Dict[str, List[Dict[str, Any]]] = {}
        with self.backend.get_connection() as conn:  # type: ignore[attr-defined]
            with conn.cursor() as cur:
                # Compact rows
                cur.execute(
                    f"""
                    SELECT data_type, data, synced_at
                    FROM connectors.connector_data
                    WHERE tenant_id = %s {where}
                    ORDER BY synced_at DESC
                    """,
                    tuple(params),
                )
                compact_rows = cur.fetchall()
                for row in compact_rows:
                    data_type = row[0]
                    data_arr = row[1] or []
                    result.setdefault(data_type, []).extend(data_arr)
                # Chunked rows
                cur.execute(
                    f"""
                    SELECT data_type, data, synced_at
                    FROM connectors.connector_data_chunks
                    WHERE tenant_id = %s {where}
                    ORDER BY synced_at DESC, chunk_index DESC
                    """,
                    tuple(params),
                )
                chunk_rows = cur.fetchall()
                for row in chunk_rows:
                    data_type = row[0]
                    data_arr = row[1] or []
                    result.setdefault(data_type, []).extend(data_arr)
        # Apply limits
        if limit_per_type is not None:
            for dt, arr in result.items():
                if len(arr) > limit_per_type:
                    result[dt] = arr[:limit_per_type]
        return result

# Convenience singleton
_store: ConnectorDataStore | None = None

def get_store() -> ConnectorDataStore:
    global _store
    if _store is None:
        _store = ConnectorDataStore()
    return _store
