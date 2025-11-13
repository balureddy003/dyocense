"""
Decision Ledger (Phase-1 skeleton, upgraded for Phase-3 dual-mode signing)

Append-only ledger to record decision actions with basic hash chaining and signatures.
Now supports HMAC (legacy) and optional asymmetric (Ed25519) via per-tenant signing keys.
Uses PostgreSQL via psycopg2 to persist entries under schema tenants.

Notes:
- HMAC path requires no external crypto deps (hashlib + hmac)
- Asymmetric path is gated by env flags and presence of tenant signing keys
- Table auto-creates on first write/read and will augment schema if needed
"""

import hmac
import json
import os
import uuid
from hashlib import sha256
from typing import Any, Dict, List, Optional, cast

# Dual-mode signing helpers (safe to import even if crypto missing)
try:
    from .signing_keys import (
        DEFAULT_SIGNATURE_MODE,
        sign_entry_auto,
        verify_entry_signature,
    )
    HAS_SIGNING_KEYS = True
except Exception:
    # Fallback strictly to HMAC if signing_keys scaffold not available
    HAS_SIGNING_KEYS = False


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
                signature TEXT,
                signing_key_id TEXT,
                signature_algorithm TEXT,
                signature_version INT
            );
            """
        )
        # Backward-compatible augmentation
        cur.execute("ALTER TABLE tenants.decision_ledger ADD COLUMN IF NOT EXISTS signing_key_id TEXT;")
        cur.execute("ALTER TABLE tenants.decision_ledger ADD COLUMN IF NOT EXISTS signature_algorithm TEXT;")
        cur.execute("ALTER TABLE tenants.decision_ledger ADD COLUMN IF NOT EXISTS signature_version INT;")

        # Create signing_keys table if not exists (lightweight scaffold)
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS tenants.signing_keys (
                id TEXT PRIMARY KEY,
                tenant_id TEXT NOT NULL,
                algorithm TEXT NOT NULL,
                public_key TEXT,
                key_vault_ref TEXT,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                expires_at TIMESTAMPTZ,
                revoked_at TIMESTAMPTZ,
                status TEXT NOT NULL DEFAULT 'active'
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
        if HAS_SIGNING_KEYS:
            sig, signing_key_id, algo = sign_entry_auto(tenant_id, chain_payload)
            entry_signature = sig
            signing_key_id_val = signing_key_id
            signature_algorithm_val = algo
            signature_version_val = 1 if algo else None
        else:
            entry_signature = _hmac_sign(chain_payload)
            signing_key_id_val = None
            signature_algorithm_val = "hmac-sha256" if entry_signature else None
            signature_version_val = None
        entry_id = f"led-{uuid.uuid4().hex[:16]}"

        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO tenants.decision_ledger (
                    id, tenant_id, action_type, source, parent_hash,
                    pre_state_hash, post_state_hash, delta_vector, metadata, signature,
                    signing_key_id, signature_algorithm, signature_version
                ) VALUES (
                    %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s,
                    %s, %s, %s
                ) RETURNING id, tenant_id, ts, action_type, source, parent_hash,
                          pre_state_hash, post_state_hash, delta_vector, metadata, signature,
                          signing_key_id, signature_algorithm, signature_version
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
                    signing_key_id_val,
                    signature_algorithm_val,
                    signature_version_val,
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
              pre_state_hash, post_state_hash, delta_vector, metadata, signature,
              signing_key_id, signature_algorithm, signature_version
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


def verify_entries(tenant_id: str, limit: int = 200) -> Dict[str, Any]:
    """Verify HMAC signatures and basic parent chain linkage for recent entries.

    Notes:
    - Signature verification requires SECRET_KEY or JWT_SECRET to be set.
    - Chain linkage check only applies when parent_hash is present; current writes may omit it.
    """
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
              pre_state_hash, post_state_hash, delta_vector, metadata, signature,
              signing_key_id, signature_algorithm, signature_version
                FROM tenants.decision_ledger
                WHERE tenant_id = %s
                ORDER BY ts ASC
                LIMIT %s
                """,
                (tenant_id, limit),
            )
            rows = cur.fetchall() or []

        secret = os.getenv("SECRET_KEY") or os.getenv("JWT_SECRET")
        results: List[Dict[str, Any]] = []
        prev_post_hash: Optional[str] = None
        overall_ok = True
        for row in rows:
            r = cast(Dict[str, Any], row)
            payload = _canonical_json(
                {
                    "tenant_id": r["tenant_id"],
                    "action_type": r["action_type"],
                    "source": r["source"],
                    "parent_hash": r["parent_hash"],
                    "pre_state_hash": r["pre_state_hash"],
                    "post_state_hash": r["post_state_hash"],
                    "delta_vector": r.get("delta_vector") or {},
                    "metadata": r.get("metadata") or {},
                }
            )

            sig_ok: Optional[bool] = None
            reason: Optional[str] = None
            # Prefer asymmetric verification if signing_key present
            signing_key_id = r.get("signing_key_id")
            sig_algo = r.get("signature_algorithm")
            signature = r.get("signature")
            if HAS_SIGNING_KEYS and signing_key_id and sig_algo and signature:
                sig_ok = verify_entry_signature(payload, signature, signing_key_id, sig_algo)
                if sig_ok is False:
                    reason = "bad-signature"
            else:
                expected_sig = _hmac_sign(payload) if secret else None
                if not secret:
                    sig_ok = None
                    reason = "no-secret"
                else:
                    sig_ok = (expected_sig == signature)
                    if not sig_ok:
                        reason = "bad-signature"

            chain_ok: Optional[bool] = None
            if r.get("parent_hash") is not None and prev_post_hash is not None:
                chain_ok = (r.get("parent_hash") == prev_post_hash)
                if overall_ok and chain_ok is False:
                    overall_ok = False

            if overall_ok and sig_ok is False:
                overall_ok = False

            results.append(
                {
                    "id": r["id"],
                    "ts": r["ts"],
                    "action_type": r["action_type"],
                    "sig_ok": sig_ok,
                    "chain_ok": chain_ok,
                    "reason": reason,
                }
            )
            prev_post_hash = r.get("post_state_hash")

        return {
            "tenant_id": tenant_id,
            "count": len(results),
            "overall_ok": overall_ok if secret else None,
            "has_secret": bool(secret),
            "entries": results,
        }
    finally:
        conn.close()


def get_integrity_summary(tenant_id: str) -> Dict[str, Any]:
    """Get a lightweight integrity summary for periodic monitoring (Phase 2).
    
    Returns high-level stats without full entry details for efficient health checks.
    """
    import psycopg2
    from psycopg2.extras import RealDictCursor
    from datetime import datetime
    
    pg_url = _get_pg_url()
    conn = psycopg2.connect(pg_url, cursor_factory=RealDictCursor)
    try:
        _ensure_table(conn)
        with conn.cursor() as cur:
            # Get count and recent entries
            cur.execute(
                """
                SELECT COUNT(*) as total_entries,
                       MIN(ts) as first_entry_ts,
                       MAX(ts) as last_entry_ts
                FROM tenants.decision_ledger
                WHERE tenant_id = %s
                """,
                (tenant_id,)
            )
            stats_row = cur.fetchone()
            stats = cast(Dict[str, Any], stats_row) if stats_row else {}
            
            # Get action type distribution
            cur.execute(
                """
                SELECT action_type, COUNT(*) as count
                FROM tenants.decision_ledger
                WHERE tenant_id = %s
                GROUP BY action_type
                ORDER BY count DESC
                """,
                (tenant_id,)
            )
            action_dist_rows = cur.fetchall() or []
        
        secret = os.getenv("SECRET_KEY") or os.getenv("JWT_SECRET")
        
        action_distribution = {}
        for row in action_dist_rows:
            r = cast(Dict[str, Any], row)
            action_distribution[r["action_type"]] = r["count"]
        
        first_ts = stats.get("first_entry_ts")
        last_ts = stats.get("last_entry_ts")
        
        return {
            "tenant_id": tenant_id,
            "total_entries": int(stats.get("total_entries", 0)),
            "first_entry": first_ts.isoformat() if first_ts else None,
            "last_entry": last_ts.isoformat() if last_ts else None,
            "action_distribution": action_distribution,
            "signature_enabled": bool(secret) or HAS_SIGNING_KEYS,
            "last_check": datetime.now().isoformat(),
        }
    finally:
        conn.close()
