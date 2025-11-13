"""
Decision Ledger (Phase-1 skeleton)

Append-only ledger to record decision actions with basic hash chaining and HMAC signature.
Uses PostgreSQL via psycopg2 to persist entries under schema tenants.

Notes:
- No external crypto dep required (uses hashlib + hmac)
- Signature uses HMAC-SHA256 with SECRET_KEY (env). If absent, signature is None.
- Table auto-creates on first write/read.
"""

import hmac
import json
import os
import uuid
from datetime import datetime
from hashlib import sha256
from typing import Any, Dict, List, Optional, cast


def _get_pg_url() -> str:
    pg_url = os.getenv("POSTGRES_URL")
    if pg_url:
        return pg_url
    pg_host = os.getenv("POSTGRES_HOST", "localhost")
    pg_port = os.getenv("POSTGRES_PORT", "5432")
    pg_db = os.getenv("POSTGRES_DB", "dyocense")
    pg_user = os.getenv("POSTGRES_USER", "dyocense")
    pg_pass = os.getenv("POSTGRES_PASSWORD", "pass@1234")
    return f"postgresql://{pg_user}:{pg_pass}@{pg_host}:{pg_port}/{pg_db}"


def _ensure_table(conn) -> None:
    with conn.cursor() as cur:
        cur.execute(
            """
            CREATE SCHEMA IF NOT EXISTS tenants;
            CREATE TABLE IF NOT EXISTS tenants.decision_ledger (
                id TEXT PRIMARY KEY,
                tenant_id TEXT NOT NULL,
                ts TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                action_type TEXT NOT NULL,
                source TEXT NOT NULL,
                parent_hash TEXT,
                pre_state_hash TEXT,
                post_state_hash TEXT,
                delta_vector JSONB,
                metadata JSONB,
                signature TEXT
            );
            """
        )


def _canonical_json(data: Optional[Dict[str, Any]]) -> str:
    if data is None:
        return "{}"
    return json.dumps(data, sort_keys=True, separators=(",", ":"))


def _hash_payload(text: str) -> str:
    return sha256(text.encode("utf-8")).hexdigest()


def _hmac_sign(text: str) -> Optional[str]:
    secret = os.getenv("SECRET_KEY") or os.getenv("JWT_SECRET")
    if not secret:
        return None
    return hmac.new(secret.encode("utf-8"), text.encode("utf-8"), sha256).hexdigest()


def append_entry(
    tenant_id: str,
    action_type: str,
    source: str,
    pre_state: Optional[Dict[str, Any]] = None,
    post_state: Optional[Dict[str, Any]] = None,
    delta_vector: Optional[Dict[str, Any]] = None,
    parent_hash: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    import psycopg2
    from psycopg2.extras import RealDictCursor, Json

    pg_url = _get_pg_url()
    conn = psycopg2.connect(pg_url, cursor_factory=RealDictCursor)
    try:
        _ensure_table(conn)

        pre_hash = _hash_payload(_canonical_json(pre_state)) if pre_state is not None else None
        post_hash = _hash_payload(_canonical_json(post_state)) if post_state is not None else None

        chain_payload = _canonical_json(
            {
                "tenant_id": tenant_id,
                "action_type": action_type,
                "source": source,
                "parent_hash": parent_hash,
                "pre_state_hash": pre_hash,
                "post_state_hash": post_hash,
                "delta_vector": delta_vector or {},
                "metadata": metadata or {},
            }
        )
        entry_signature = _hmac_sign(chain_payload)
        entry_id = f"led-{uuid.uuid4().hex[:16]}"

        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO tenants.decision_ledger (
                    id, tenant_id, action_type, source, parent_hash,
                    pre_state_hash, post_state_hash, delta_vector, metadata, signature
                ) VALUES (
                    %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s
                ) RETURNING id, tenant_id, ts, action_type, source, parent_hash,
                          pre_state_hash, post_state_hash, delta_vector, metadata, signature
                """,
                (
                    entry_id,
                    tenant_id,
                    action_type,
                    source,
                    parent_hash,
                    pre_hash,
                    post_hash,
                    Json(delta_vector or {}),
                    Json(metadata or {}),
                    entry_signature,
                ),
            )
            row = cur.fetchone()
            conn.commit()
            if row is None:
                raise RuntimeError("Failed to insert ledger entry (no row returned)")
            return cast(Dict[str, Any], row)
    finally:
        conn.close()


def get_chain(tenant_id: str, limit: int = 50) -> List[Dict[str, Any]]:
    import psycopg2
    from psycopg2.extras import RealDictCursor

    pg_url = _get_pg_url()
    conn = psycopg2.connect(pg_url, cursor_factory=RealDictCursor)
    try:
        _ensure_table(conn)
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, tenant_id, ts, action_type, source, parent_hash,
                       pre_state_hash, post_state_hash, delta_vector, metadata, signature
                FROM tenants.decision_ledger
                WHERE tenant_id = %s
                ORDER BY ts DESC
                LIMIT %s
                """,
                (tenant_id, limit),
            )
            rows = cur.fetchall() or []
        return [cast(Dict[str, Any], r) for r in rows]
    finally:
        conn.close()

"""
Decision Ledger (Phase-1 skeleton)

Append-only ledger to record decision actions with basic hash chaining and HMAC signature.
Uses PostgreSQL via psycopg2 to persist entries under schema tenants.

Notes:
- No external crypto dep required (uses hashlib + hmac)
- Signature uses HMAC-SHA256 with SECRET_KEY (env). If absent, signature is None.
- Table auto-creates on first write/read.
"""
import hmac
import json
import os
import uuid
from datetime import datetime
from hashlib import sha256
from typing import Any, Dict, List, Optional, cast
    
    pg_url = _get_pg_url()
    conn = psycopg2.connect(pg_url, cursor_factory=RealDictCursor)
    try:
        _ensure_table(conn)

        pre_hash = _hash_payload(_canonical_json(pre_state)) if pre_state is not None else None
        post_hash = _hash_payload(_canonical_json(post_state)) if post_state is not None else None

        chain_payload = _canonical_json(
            {
                "tenant_id": tenant_id,
                "action_type": action_type,
                "source": source,
                "parent_hash": parent_hash,
                "pre_state_hash": pre_hash,
                "post_state_hash": post_hash,
                "delta_vector": delta_vector or {},
                "metadata": metadata or {},
            }
        )
        entry_signature = _hmac_sign(chain_payload)
        entry_id = f"led-{uuid.uuid4().hex[:16]}"

        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO tenants.decision_ledger (
                    id, tenant_id, action_type, source, parent_hash,
                    pre_state_hash, post_state_hash, delta_vector, metadata, signature
                ) VALUES (
                    %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s
                ) RETURNING id, tenant_id, ts, action_type, source, parent_hash,
                          pre_state_hash, post_state_hash, delta_vector, metadata, signature
                """,
                (
                    entry_id,
                    tenant_id,
                    action_type,
                    source,
                    parent_hash,
                    pre_hash,
                    post_hash,
                    Json(delta_vector or {}),
                    Json(metadata or {}),
                    entry_signature,
                ),
            )
            row = cur.fetchone()
            conn.commit()
            if row is None:
                raise RuntimeError("Failed to insert ledger entry (no row returned)")
            return cast(Dict[str, Any], row)
    finally:
        conn.close()


def get_chain(tenant_id: str, limit: int = 50) -> List[Dict[str, Any]]:
    import psycopg2
    from psycopg2.extras import RealDictCursor

    pg_url = _get_pg_url()
    conn = psycopg2.connect(pg_url, cursor_factory=RealDictCursor)
    try:
        _ensure_table(conn)
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, tenant_id, ts, action_type, source, parent_hash,
                       pre_state_hash, post_state_hash, delta_vector, metadata, signature
                FROM tenants.decision_ledger
                WHERE tenant_id = %s
                ORDER BY ts DESC
                LIMIT %s
                """,
                (tenant_id, limit),
            )
            rows = cur.fetchall() or []
        return [cast(Dict[str, Any], r) for r in rows]
    finally:
        conn.close()
"""
Decision Ledger (P0 scaffold)

Append-only, hash-chained in-memory ledger with optional persistence hooks.
Provides basic commit/list APIs for early UX and future DB backing.
"""
from __future__ import annotations

import hashlib
import time
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Any


@dataclass
class LedgerEntry:
    id: str
    tenant_id: str
    ts: float
    action_type: str
    source: str
    payload: Dict[str, Any]
    parent_hash: Optional[str]
    self_hash: str


# Simple in-memory store: {tenant_id: [LedgerEntry, ...]}
_STORE: Dict[str, List[LedgerEntry]] = {}


def _hash_entry(tenant_id: str, ts: float, action_type: str, source: str, payload: Dict[str, Any], parent_hash: Optional[str]) -> str:
    m = hashlib.sha256()
    m.update(tenant_id.encode('utf-8'))
    m.update(str(ts).encode('utf-8'))
    m.update(action_type.encode('utf-8'))
    m.update(source.encode('utf-8'))
    m.update(parent_hash.encode('utf-8') if parent_hash else b'')
    # Deterministic payload hashing
    import json
    m.update(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode('utf-8'))
    return m.hexdigest()


def commit(tenant_id: str, action_type: str, source: str, payload: Dict[str, Any]) -> LedgerEntry:
    chain = _STORE.setdefault(tenant_id, [])
    parent_hash = chain[-1].self_hash if chain else None
    ts = time.time()
    entry_id = str(int(ts * 1000))
    h = _hash_entry(tenant_id, ts, action_type, source, payload, parent_hash)
    entry = LedgerEntry(
        id=entry_id,
        tenant_id=tenant_id,
        ts=ts,
        action_type=action_type,
        source=source,
        payload=payload,
        parent_hash=parent_hash,
        self_hash=h,
    )
    chain.append(entry)
    return entry


def list_chain(tenant_id: str, limit: int = 100) -> List[Dict[str, Any]]:
    chain = _STORE.get(tenant_id, [])
    return [asdict(e) for e in chain[-limit:]][::-1]


def last_n_attributions(tenant_id: str, n: int = 10) -> List[Dict[str, Any]]:
    """Return most recent entries related to health-score impact (if present)."""
    chain = _STORE.get(tenant_id, [])
    out: List[Dict[str, Any]] = []
    for e in reversed(chain):
        if e.action_type in {"task_completed", "goal_created", "coach_recommendation", "optimization_decision"}:
            impact = e.payload.get("delta", {})
            out.append({
                "id": e.id,
                "ts": e.ts,
                "action_type": e.action_type,
                "source": e.source,
                "delta": impact,
            })
            if len(out) >= n:
                break
    return out
