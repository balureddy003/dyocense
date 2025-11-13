from __future__ import annotations

import os
import uuid
from typing import Optional, Tuple, Any, cast

from .models import SigningKey, KeyAlgorithm

# Optional cryptography imports
try:
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric import ed25519
    from cryptography.hazmat.backends import default_backend
    HAS_CRYPTO = True
except Exception:  # ImportError or other
    HAS_CRYPTO = False
    serialization = None
    ed25519 = None
    default_backend = None


# Environment-driven defaults
_ENV = os.getenv("ENV", os.getenv("PY_ENV", "dev")).lower()
_DEFAULT_IN_DEV = "hmac"
DEFAULT_SIGNATURE_MODE = os.getenv(
    "DEFAULT_SIGNATURE_MODE",
    _DEFAULT_IN_DEV if _ENV in ("dev", "development", "local") else "auto",
).lower()
ENABLE_ASYMMETRIC_SIGNING = os.getenv("ENABLE_ASYMMETRIC_SIGNING", "").lower() in ("1", "true", "yes")
ALLOW_DEV_KEY_GEN = os.getenv("ALLOW_DEV_KEY_GEN", "").lower() in ("1", "true", "yes")


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


def tenant_has_signing_key(tenant_id: str) -> bool:
    """Return True if tenant has an active asymmetric signing key.
    Safe to call even if table doesn't yet exist (returns False).
    """
    import psycopg2
    from psycopg2.extras import RealDictCursor

    if not ENABLE_ASYMMETRIC_SIGNING:
        return False

    pg_url = _get_pg_url()
    try:
        conn = psycopg2.connect(pg_url, cursor_factory=RealDictCursor)
    except Exception:
        return False

    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT 1
                FROM information_schema.tables
                WHERE table_schema='tenants' AND table_name='signing_keys'
                """
            )
            if cur.fetchone() is None:
                return False

            cur.execute(
                """
                SELECT id
                FROM tenants.signing_keys
                WHERE tenant_id = %s AND status = 'active'
                LIMIT 1
                """,
                (tenant_id,),
            )
            return cur.fetchone() is not None
    except Exception:
        return False
    finally:
        try:
            conn.close()
        except Exception:
            pass


def get_active_signing_key(tenant_id: str) -> Optional[SigningKey]:
    """Fetch active signing key metadata for tenant.
    Returns None if not present or asymmetric disabled.
    """
    import psycopg2
    from psycopg2.extras import RealDictCursor

    if not ENABLE_ASYMMETRIC_SIGNING:
        return None

    pg_url = _get_pg_url()
    conn = psycopg2.connect(pg_url, cursor_factory=RealDictCursor)
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, tenant_id, algorithm, public_key, key_vault_ref, status
                FROM tenants.signing_keys
                WHERE tenant_id = %s AND status = 'active'
                ORDER BY created_at DESC
                LIMIT 1
                """,
                (tenant_id,),
            )
            row = cur.fetchone()
            if not row:
                return None
            row_d: dict[str, Any] = row if isinstance(row, dict) else dict(row)
            algo = KeyAlgorithm(row_d.get("algorithm", KeyAlgorithm.ed25519)) if isinstance(row_d.get("algorithm"), str) else KeyAlgorithm.ed25519
            return SigningKey(
                id=cast(str, row_d.get("id")),
                tenant_id=cast(str, row_d.get("tenant_id")),
                algorithm=algo,
                public_key_pem=row_d.get("public_key"),
                key_vault_ref=row_d.get("key_vault_ref"),
                status=row_d.get("status", "active"),
            )
    finally:
        conn.close()


def list_tenant_keys(tenant_id: str) -> list[dict[str, Any]]:
    """List all signing keys for a tenant (metadata only)."""
    import psycopg2
    from psycopg2.extras import RealDictCursor

    pg_url = _get_pg_url()
    conn = psycopg2.connect(pg_url, cursor_factory=RealDictCursor)
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, tenant_id, algorithm, public_key, key_vault_ref, status, created_at, expires_at, revoked_at
                FROM tenants.signing_keys
                WHERE tenant_id = %s
                ORDER BY created_at DESC
                """,
                (tenant_id,),
            )
            rows = cur.fetchall() or []
            return [dict(r) for r in rows]
    finally:
        conn.close()


def register_public_key(
    tenant_id: str,
    algorithm: str,
    public_key_pem: str,
    set_active: bool = True,
    key_vault_ref: Optional[str] = None,
) -> str:
    """Register a public key for a tenant. Returns key id.
    If set_active=True, previous active keys are expired.
    """
    import psycopg2
    from psycopg2.extras import RealDictCursor

    key_id = f"key-{tenant_id}-{uuid.uuid4().hex[:8]}"
    pg_url = _get_pg_url()
    conn = psycopg2.connect(pg_url, cursor_factory=RealDictCursor)
    try:
        with conn.cursor() as cur:
            if set_active:
                cur.execute(
                    """
                    UPDATE tenants.signing_keys
                    SET status = 'expired', expires_at = NOW()
                    WHERE tenant_id = %s AND status = 'active'
                    """,
                    (tenant_id,),
                )

            cur.execute(
                """
                INSERT INTO tenants.signing_keys (id, tenant_id, algorithm, public_key, key_vault_ref, status)
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (key_id, tenant_id, algorithm, public_key_pem, key_vault_ref, 'active' if set_active else 'revoked'),
            )
            conn.commit()
        return key_id
    finally:
        conn.close()


def set_key_status(tenant_id: str, key_id: str, status: str) -> bool:
    """Set key status to active|expired|revoked. If activating, expire others."""
    import psycopg2
    from psycopg2.extras import RealDictCursor

    if status not in ("active", "expired", "revoked"):
        return False

    pg_url = _get_pg_url()
    conn = psycopg2.connect(pg_url, cursor_factory=RealDictCursor)
    try:
        with conn.cursor() as cur:
            if status == "active":
                cur.execute(
                    """
                    UPDATE tenants.signing_keys
                    SET status = 'expired', expires_at = NOW()
                    WHERE tenant_id = %s AND status = 'active' AND id <> %s
                    """,
                    (tenant_id, key_id),
                )
            cur.execute(
                """
                UPDATE tenants.signing_keys
                SET status = %s,
                    expires_at = CASE WHEN %s='expired' THEN NOW() ELSE expires_at END,
                    revoked_at = CASE WHEN %s='revoked' THEN NOW() ELSE revoked_at END
                WHERE tenant_id = %s AND id = %s
                """,
                (status, status, status, tenant_id, key_id),
            )
            conn.commit()
            return True
    finally:
        conn.close()


def rotate_signing_key(tenant_id: str, new_public_key_pem: str, algorithm: str = KeyAlgorithm.ed25519.value) -> str:
    """Expire current active key and insert a new active key with provided public key."""
    return register_public_key(tenant_id, algorithm, new_public_key_pem, set_active=True)


# --- Ed25519 helpers (dev convenience) ---

def _sign_ed25519_with_env_key(payload: str) -> Optional[str]:
    """Sign using ED25519_PRIVATE_KEY_PEM from env (dev convenience).
    Returns hex signature or None if not possible.
    """
    if not HAS_CRYPTO:
        return None
    private_pem = os.getenv("ED25519_PRIVATE_KEY_PEM")
    if not private_pem:
        return None
    try:
        private_key = cast(Any, serialization).load_pem_private_key(
            private_pem.encode("utf-8"), password=None
        )
        sig = cast(Any, private_key).sign(payload.encode("utf-8"))
        return sig.hex()
    except Exception:
        return None


def _verify_ed25519_with_public_key(payload: str, signature_hex: str, public_key_pem: str) -> bool:
    if not HAS_CRYPTO:
        return False
    try:
        public_key = cast(Any, serialization).load_pem_public_key(public_key_pem.encode("utf-8"))
        cast(Any, public_key).verify(bytes.fromhex(signature_hex), payload.encode("utf-8"))
        return True
    except Exception:
        return False


# --- Dual-mode API used by ledger ---

def sign_entry_auto(
    tenant_id: str,
    payload: str,
    mode: str = DEFAULT_SIGNATURE_MODE,
) -> Tuple[Optional[str], Optional[str], str]:
    """Sign payload per mode.
    Returns: (signature, signing_key_id, algorithm)
    algorithm is always a string (e.g., 'hmac-sha256', 'ed25519').
    """
    # Legacy HMAC signer sourced from decision_ledger_pg.py secret
    import hmac
    from hashlib import sha256

    # Mode resolution
    selected_mode = (mode or "auto").lower()
    if selected_mode == "auto":
        selected_mode = "asymmetric" if tenant_has_signing_key(tenant_id) else "hmac"

    # HMAC path (always available)
    if selected_mode == "hmac" or not ENABLE_ASYMMETRIC_SIGNING:
        secret = os.getenv("SECRET_KEY") or os.getenv("JWT_SECRET")
        if not secret:
            return None, None, KeyAlgorithm.hmac_sha256.value
        sig = hmac.new(secret.encode("utf-8"), payload.encode("utf-8"), sha256).hexdigest()
        return sig, None, KeyAlgorithm.hmac_sha256.value

    # Asymmetric path
    key = get_active_signing_key(tenant_id)
    if not key:
        # fallback to HMAC if no key
        secret = os.getenv("SECRET_KEY") or os.getenv("JWT_SECRET")
        if not secret:
            return None, None, KeyAlgorithm.hmac_sha256.value
        sig = hmac.new(secret.encode("utf-8"), payload.encode("utf-8"), sha256).hexdigest()
        return sig, None, KeyAlgorithm.hmac_sha256.value

    # For dev, allow signing with env private key; in prod, keys should be in KMS/Vault (not implemented here)
    signature = _sign_ed25519_with_env_key(payload) if key.algorithm == KeyAlgorithm.ed25519 else None
    if signature:
        return signature, key.id, key.algorithm.value

    # If we cannot sign asymmetrically (no private key path), fallback to HMAC
    secret = os.getenv("SECRET_KEY") or os.getenv("JWT_SECRET")
    if not secret:
        return None, None, KeyAlgorithm.hmac_sha256.value
    sig = hmac.new(secret.encode("utf-8"), payload.encode("utf-8"), sha256).hexdigest()
    return sig, None, KeyAlgorithm.hmac_sha256.value


def verify_entry_signature(
    payload: str,
    signature: Optional[str],
    signing_key_id: Optional[str],
    algorithm: Optional[str],
) -> Optional[bool]:
    """Verify signature; returns True/False, or None if cannot verify (no secret & no key).
    """
    if not signature:
        return None

    # Asymmetric verification if we have a key id and algorithm
    if signing_key_id and algorithm:
        key = get_key_by_id(signing_key_id)
        if not key:
            return False
        if algorithm == KeyAlgorithm.ed25519.value and key.public_key_pem:
            return _verify_ed25519_with_public_key(payload, signature, key.public_key_pem)
        # Unknown algorithm paths not supported yet
        return False

    # Legacy HMAC verification
    import hmac
    from hashlib import sha256

    secret = os.getenv("SECRET_KEY") or os.getenv("JWT_SECRET")
    if not secret:
        return None
    expected = hmac.new(secret.encode("utf-8"), payload.encode("utf-8"), sha256).hexdigest()
    return expected == signature


def get_key_by_id(signing_key_id: str) -> Optional[SigningKey]:
    import psycopg2
    from psycopg2.extras import RealDictCursor

    if not ENABLE_ASYMMETRIC_SIGNING:
        return None

    pg_url = _get_pg_url()
    conn = psycopg2.connect(pg_url, cursor_factory=RealDictCursor)
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, tenant_id, algorithm, public_key, key_vault_ref, status
                FROM tenants.signing_keys
                WHERE id = %s
                LIMIT 1
                """,
                (signing_key_id,),
            )
            row = cur.fetchone()
            if not row:
                return None
            row_d: dict[str, Any] = row if isinstance(row, dict) else dict(row)
            algo = KeyAlgorithm(row_d.get("algorithm", KeyAlgorithm.ed25519)) if isinstance(row_d.get("algorithm"), str) else KeyAlgorithm.ed25519
            return SigningKey(
                id=cast(str, row_d.get("id")),
                tenant_id=cast(str, row_d.get("tenant_id")),
                algorithm=algo,
                public_key_pem=row_d.get("public_key"),
                key_vault_ref=row_d.get("key_vault_ref"),
                status=row_d.get("status", "active"),
            )
    finally:
        conn.close()
