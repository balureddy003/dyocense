"""Quick manual test for chunked connector data ingestion and retrieval.
Run with: python scripts/test_chunk_ingestion.py
Requires PostgresBackend configured (PERSISTENCE_BACKEND=postgres etc.)
"""
from __future__ import annotations

import os
import random
import string
from datetime import datetime

from packages.connectors.data_store_pg import get_store
from packages.kernel_common.persistence_v2 import get_backend, PostgresBackend

TENANT = os.getenv("TEST_TENANT_ID", "tenant_demo")
CONNECTOR = os.getenv("TEST_CONNECTOR_ID", "csv_bulk_1")
RECORDS = int(os.getenv("TEST_RECORDS", "16000"))

# Synthetic record generator

def make_record(i: int):
    return {
        "row": i,
        "sku": f"SKU-{i:05d}",
        "qty": random.randint(0, 500),
        "price": round(random.uniform(1, 250), 2),
        "category": random.choice(["tools", "outdoor", "parts", "misc"]),
        "ts": datetime.utcnow().isoformat(),
        "note": ''.join(random.choices(string.ascii_lowercase, k=12)),
    }


def main():
    backend = get_backend()
    if not isinstance(backend, PostgresBackend):
        print("Postgres backend not active; aborting test")
        return
    store = get_store()
    records = [make_record(i) for i in range(RECORDS)]
    print(f"Ingesting {len(records)} records (chunk threshold={store.DEFAULT_CHUNK_SIZE if hasattr(store,'DEFAULT_CHUNK_SIZE') else 'internal'})")
    meta = {"source": "synthetic_test", "generator": "test_chunk_ingestion.py"}
    res = store.ingest(TENANT, CONNECTOR, "inventory", records, meta)
    print("Ingestion result:", res)
    fetched = store.fetch_all(TENANT, connector_ids=[CONNECTOR], data_types=["inventory"], limit_per_type=None)
    print("Fetched types:", list(fetched.keys()))
    print("Fetched inventory count:", len(fetched.get("inventory", [])))
    # Show first 2 records for sanity
    sample = fetched.get("inventory", [])[:2]
    print("Sample records:", sample)


if __name__ == "__main__":
    main()
