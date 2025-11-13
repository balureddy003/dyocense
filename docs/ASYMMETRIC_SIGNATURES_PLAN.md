# Asymmetric Signatures for Decision Ledger (Phase 3+ Planning)

**Status:** Design/Planning Document  
**Target:** Future Implementation (Post-Phase 3)  
**Priority:** Medium (enhances security but not critical for MVP)

---

## Overview

This document outlines the design for migrating the decision ledger from HMAC-based symmetric signatures to RSA/Ed25519-based asymmetric signatures. This enhancement provides:

- **Non-repudiation**: Only the private key holder can sign entries
- **Per-tenant isolation**: Each tenant has their own keypair
- **Key rotation**: Easier to rotate without recomputing all signatures
- **Audit compliance**: Stronger cryptographic guarantees for compliance

---

## Current State (Phase 1-2)

### HMAC Signatures

**Implementation:**

```python
# Current approach (decision_ledger_pg.py)
def _hmac_sign(text: str) -> Optional[str]:
    secret = os.getenv("SECRET_KEY") or os.getenv("JWT_SECRET")
    if not secret:
        return None
    return hmac.new(
        secret.encode("utf-8"),
        text.encode("utf-8"),
        sha256
    ).hexdigest()
```

**Pros:**

- ✅ Simple implementation
- ✅ Fast computation
- ✅ No external dependencies
- ✅ Works with shared secret

**Cons:**

- ❌ Symmetric key (anyone with secret can sign)
- ❌ Single secret for all tenants
- ❌ Rotation requires re-signing all entries
- ❌ No non-repudiation

---

## Proposed Design

### Architecture

```text
┌─────────────────────────────────────────────────┐
│ Tenant Key Management Service                  │
├─────────────────────────────────────────────────┤
│                                                 │
│  ┌──────────────────┐   ┌──────────────────┐  │
│  │  Key Generation  │   │  Key Storage     │  │
│  │  - RSA-2048/4096 │   │  - Azure KeyVault│  │
│  │  - Ed25519       │   │  - AWS KMS       │  │
│  │  - Per-tenant    │   │  - HashiCorp Vault│ │
│  └──────────────────┘   └──────────────────┘  │
│                                                 │
│  ┌──────────────────┐   ┌──────────────────┐  │
│  │  Key Rotation    │   │  Verification    │  │
│  │  - Scheduled     │   │  - Public key    │  │
│  │  - On-demand     │   │  - Multi-version │  │
│  └──────────────────┘   └──────────────────┘  │
│                                                 │
└─────────────────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────┐
│ Decision Ledger (tenants.decision_ledger)      │
├─────────────────────────────────────────────────┤
│  - id                                           │
│  - tenant_id                                    │
│  - signature (RSA/Ed25519)                      │
│  - signing_key_id (for rotation)                │
│  - signature_algorithm (rsa-sha256, ed25519)    │
│  - ...existing fields...                        │
└─────────────────────────────────────────────────┘
```

### Database Schema Changes

**Add columns to `tenants.decision_ledger`:**

```sql
ALTER TABLE tenants.decision_ledger
  ADD COLUMN signing_key_id TEXT,
  ADD COLUMN signature_algorithm TEXT,
  ADD COLUMN signature_version INT DEFAULT 1;
```

**Create tenant keys table:**

```sql
CREATE TABLE tenants.signing_keys (
    id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL,
    algorithm TEXT NOT NULL,  -- 'rsa-2048', 'rsa-4096', 'ed25519'
    public_key TEXT NOT NULL,  -- PEM format
    key_vault_ref TEXT,  -- Reference to external key vault
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMPTZ,
    revoked_at TIMESTAMPTZ,
    status TEXT NOT NULL,  -- 'active', 'expired', 'revoked'
    UNIQUE(tenant_id, created_at)
);

CREATE INDEX idx_signing_keys_tenant ON tenants.signing_keys(tenant_id);
CREATE INDEX idx_signing_keys_status ON tenants.signing_keys(status);
```

---

## Implementation Plan

### Phase 1: Infrastructure Setup

**Tasks:**

1. Create `tenants.signing_keys` table
2. Implement key generation service
3. Add key vault integration (Azure KeyVault or AWS KMS)
4. Build key rotation scheduler

**Dependencies:**

```python
# New dependencies
cryptography>=41.0.0  # RSA/Ed25519 support
azure-keyvault-keys>=4.8.0  # For Azure KeyVault (optional)
boto3>=1.28.0  # For AWS KMS (optional)
```

**Code Structure:**

```text
services/smb_gateway/
├── signing_keys/
│   ├── __init__.py
│   ├── key_manager.py        # Key generation, storage
│   ├── key_rotation.py       # Rotation logic
│   ├── vault_adapter.py      # Key vault integration
│   └── models.py             # SigningKey, KeyAlgorithm models
```

### Phase 2: Dual-Mode Operation

**Strategy:** Support both HMAC and asymmetric signatures during migration.

**Implementation:**

```python
def _sign_entry(
    tenant_id: str,
    payload: str,
    mode: str = "auto"  # 'hmac', 'asymmetric', 'auto'
) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """Sign ledger entry with appropriate method.
    
    Returns:
        (signature, signing_key_id, algorithm)
    """
    # Auto mode: prefer asymmetric if key available
    if mode == "auto":
        if tenant_has_signing_key(tenant_id):
            mode = "asymmetric"
        else:
            mode = "hmac"
    
    if mode == "asymmetric":
        key = get_active_signing_key(tenant_id)
        if not key:
            raise ValueError(f"No active signing key for tenant {tenant_id}")
        
        signature = _sign_with_private_key(payload, key)
        return signature, key.id, key.algorithm
    
    else:  # hmac (legacy)
        signature = _hmac_sign(payload)
        return signature, None, "hmac-sha256"


def _verify_entry(
    signature: str,
    payload: str,
    signing_key_id: Optional[str],
    algorithm: Optional[str],
) -> bool:
    """Verify signature using appropriate method."""
    if signing_key_id:
        # Asymmetric verification
        key = get_signing_key(signing_key_id)
        return _verify_with_public_key(payload, signature, key.public_key)
    else:
        # Legacy HMAC verification
        expected = _hmac_sign(payload)
        return signature == expected
```

### Phase 3: Migration

**Migration Steps:**

1. **Enable asymmetric for new entries**
   - Set `DEFAULT_SIGNATURE_MODE=asymmetric`
   - Generate keys for all existing tenants

2. **Background re-signing** (optional)
   - Read old HMAC entries
   - Re-sign with asymmetric keys
   - Update signature columns
   - Maintain old signature in `legacy_signature` column for audit

3. **Deprecate HMAC** (after migration period)
   - Remove HMAC fallback code
   - Drop `legacy_signature` column
   - Update verification to assume asymmetric

**Timeline:**

- Week 1-2: Infrastructure setup
- Week 3-4: Dual-mode implementation
- Week 5-8: Gradual tenant migration
- Week 9+: HMAC deprecation

---

## Key Generation

### Algorithm Choice

**RSA-2048:**

- ✅ Widely supported
- ✅ FIPS-compliant
- ❌ Slower signing/verification
- ❌ Larger signature size

**Ed25519:**

- ✅ Fast signing/verification
- ✅ Small signature size (64 bytes)
- ✅ Modern, secure
- ❌ Less universal support (but Python cryptography lib supports it)

**Recommendation:** Start with Ed25519 for new tenants, support RSA for compatibility.

### Rotation Code Example

```python
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ed25519, rsa
from cryptography.hazmat.backends import default_backend

def generate_ed25519_keypair(tenant_id: str) -> Tuple[str, str]:
    """Generate Ed25519 keypair for tenant.
    
    Returns:
        (private_key_pem, public_key_pem)
    """
    private_key = ed25519.Ed25519PrivateKey.generate()
    public_key = private_key.public_key()
    
    # Serialize to PEM
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    ).decode('utf-8')
    
    public_pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    ).decode('utf-8')
    
    return private_pem, public_pem


def sign_with_ed25519(payload: str, private_key_pem: str) -> str:
    """Sign payload with Ed25519 private key."""
    private_key = serialization.load_pem_private_key(
        private_key_pem.encode('utf-8'),
        password=None,
        backend=default_backend()
    )
    
    signature = private_key.sign(payload.encode('utf-8'))
    return signature.hex()


def verify_ed25519(payload: str, signature_hex: str, public_key_pem: str) -> bool:
    """Verify Ed25519 signature."""
    public_key = serialization.load_pem_public_key(
        public_key_pem.encode('utf-8'),
        backend=default_backend()
    )
    
    try:
        public_key.verify(
            bytes.fromhex(signature_hex),
            payload.encode('utf-8')
        )
        return True
    except Exception:
        return False
```

---

## Key Storage Options

### Option 1: Database (Simple)

**Pros:**

- ✅ Easy to implement
- ✅ No external dependencies
- ✅ Works in dev/test

**Cons:**

- ❌ Private keys in DB (security risk)
- ❌ Need encryption at rest
- ❌ Not HSM-backed

**Use Case:** Development, small deployments

### Option 2: Azure Key Vault (Recommended for Azure)

**Pros:**

- ✅ HSM-backed keys
- ✅ Managed service
- ✅ Key rotation built-in
- ✅ Audit logging

**Cons:**

- ❌ Cost (~$0.03 per 10K operations)
- ❌ Azure-specific

**Integration:**

```python
from azure.identity import DefaultAzureCredential
from azure.keyvault.keys import KeyClient
from azure.keyvault.keys.crypto import CryptographyClient, SignatureAlgorithm

async def sign_with_keyvault(
    tenant_id: str,
    payload: str,
    key_name: str
) -> str:
    """Sign using Azure Key Vault."""
    credential = DefaultAzureCredential()
    key_client = KeyClient(
        vault_url=f"https://{KEY_VAULT_NAME}.vault.azure.net/",
        credential=credential
    )
    
    key = key_client.get_key(key_name)
    crypto_client = CryptographyClient(key, credential=credential)
    
    result = await crypto_client.sign(
        SignatureAlgorithm.rs256,
        payload.encode('utf-8')
    )
    
    return result.signature.hex()
```

### Option 3: AWS KMS (For AWS deployments)

Similar to Azure Key Vault but using AWS services.

### Option 4: HashiCorp Vault (Multi-cloud)

Portable across cloud providers.

---

## Key Rotation

### Rotation Triggers

- **Scheduled:** Every 90 days (configurable)
- **On-demand:** Admin action
- **Security event:** Suspected compromise

### Rotation Process

1. **Generate new keypair** for tenant
2. **Update `tenants.signing_keys`:**
   - Mark old key as `status='expired'`
   - Insert new key with `status='active'`
3. **New entries use new key** automatically
4. **Old entries remain valid** (verified with old public key)
5. **Optional re-signing:** Background job re-signs old entries

### Code Example

```python
async def rotate_signing_key(tenant_id: str) -> str:
    """Rotate signing key for tenant.
    
    Returns:
        New signing_key_id
    """
    # Generate new keypair
    private_pem, public_pem = generate_ed25519_keypair(tenant_id)
    
    # Store in key vault (or DB)
    key_id = f"key-{tenant_id}-{uuid.uuid4().hex[:8]}"
    
    async with get_db_connection() as conn:
        # Expire old keys
        await conn.execute(
            """
            UPDATE tenants.signing_keys
            SET status = 'expired', expires_at = NOW()
            WHERE tenant_id = %s AND status = 'active'
            """,
            (tenant_id,)
        )
        
        # Insert new key
        await conn.execute(
            """
            INSERT INTO tenants.signing_keys
            (id, tenant_id, algorithm, public_key, status)
            VALUES (%s, %s, 'ed25519', %s, 'active')
            """,
            (key_id, tenant_id, public_pem)
        )
    
    # Log rotation event
    logger.info(f"[key_rotation] Rotated key for tenant {tenant_id} -> {key_id}")
    
    return key_id
```

---

## Verification Updates

### Multi-Version Verification

The ledger must support verifying entries signed with different keys:

```python
def verify_ledger_entry(entry: Dict[str, Any]) -> bool:
    """Verify ledger entry signature (supports multiple key versions)."""
    signature = entry.get("signature")
    signing_key_id = entry.get("signing_key_id")
    algorithm = entry.get("signature_algorithm", "hmac-sha256")
    
    # Reconstruct canonical payload
    payload = _canonical_json({
        "tenant_id": entry["tenant_id"],
        "action_type": entry["action_type"],
        "source": entry["source"],
        "parent_hash": entry.get("parent_hash"),
        "pre_state_hash": entry.get("pre_state_hash"),
        "post_state_hash": entry.get("post_state_hash"),
        "delta_vector": entry.get("delta_vector") or {},
        "metadata": entry.get("metadata") or {},
    })
    
    if signing_key_id:
        # Asymmetric verification
        key = get_signing_key(signing_key_id)
        if not key:
            return False
        
        if algorithm == "ed25519":
            return verify_ed25519(payload, signature, key.public_key)
        elif algorithm.startswith("rsa-"):
            return verify_rsa(payload, signature, key.public_key)
        else:
            return False
    else:
        # Legacy HMAC verification
        expected = _hmac_sign(payload)
        return signature == expected
```

---

## Rollback Plan

### If Issues Arise

1. **Signature failures:**
   - Switch `DEFAULT_SIGNATURE_MODE` back to `hmac`
   - Disable asymmetric signing temporarily

2. **Key vault issues:**
   - Fallback to DB-stored keys
   - Cache public keys for verification

3. **Performance issues:**
   - Increase key cache TTL
   - Use async signing where possible

### Rollback Procedure

```bash
# Disable asymmetric signatures
export DEFAULT_SIGNATURE_MODE=hmac

# Restart services
docker-compose restart smb-gateway

# Verify HMAC signing working
curl -X POST ".../ledger/commit" \
  -d '{"action_type": "test", "source": "admin"}'

# Check signature in DB
psql -c "SELECT signature, signing_key_id FROM tenants.decision_ledger ORDER BY ts DESC LIMIT 1;"
# signing_key_id should be NULL (HMAC mode)
```

---

## Security Considerations

### Private Key Protection

- **Never log private keys**
- **Encrypt at rest** if stored in DB
- **Use HSM** (Key Vault/KMS) in production
- **Rotate regularly** (90 days default)
- **Revoke on compromise** immediately

### Audit Trail

- **Log all key operations:**
  - Generation
  - Rotation
  - Revocation
  - Access

- **Monitor verification failures:**
  - Alert on high failure rate
  - Track invalid signatures
  - Investigate anomalies

### Access Control

- **Signing:** Only backend services (never client-side)
- **Verification:** Public keys can be exposed for audit
- **Key management:** Admin-only operations
- **Rotation:** Automated + emergency manual

---

## Testing Strategy

### Unit Tests

```python
def test_ed25519_sign_verify():
    """Test Ed25519 signing and verification."""
    private_pem, public_pem = generate_ed25519_keypair("test-tenant")
    payload = "test payload"
    
    signature = sign_with_ed25519(payload, private_pem)
    assert verify_ed25519(payload, signature, public_pem)
    
    # Wrong payload should fail
    assert not verify_ed25519("wrong", signature, public_pem)

def test_key_rotation():
    """Test key rotation maintains verification."""
    tenant_id = "test-tenant"
    
    # Sign with old key
    old_key_id = generate_signing_key(tenant_id)
    old_signature = sign_entry(tenant_id, "payload1", old_key_id)
    
    # Rotate key
    new_key_id = rotate_signing_key(tenant_id)
    
    # Sign with new key
    new_signature = sign_entry(tenant_id, "payload2", new_key_id)
    
    # Both should verify
    assert verify_entry("payload1", old_signature, old_key_id)
    assert verify_entry("payload2", new_signature, new_key_id)
```

### Integration Tests

- Sign and verify entries end-to-end
- Test key rotation during active signing
- Verify integrity endpoint with mixed signatures
- Test fallback to HMAC when key unavailable

---

## Cost Analysis

### Azure Key Vault

- **Key storage:** $1/key/month
- **Operations:** $0.03 per 10K operations
- **HSM-backed:** Add $1/month per key

**Estimate for 100 tenants:**

- 100 keys × $1/month = $100/month
- 1M operations/month ÷ 10K × $0.03 = $3/month
- **Total:** ~$103/month

### AWS KMS

Similar pricing structure to Azure.

### Self-Hosted Vault

- **Infrastructure:** ~$50-100/month (VM + storage)
- **Maintenance:** Engineering time

---

## Migration Checklist

- [ ] Add `signing_keys` table
- [ ] Implement key generation (Ed25519 + RSA)
- [ ] Integrate with key vault (Azure/AWS/Vault)
- [ ] Update `decision_ledger` schema (add columns)
- [ ] Implement dual-mode signing
- [ ] Update verification logic
- [ ] Add key rotation scheduler
- [ ] Create admin key management UI
- [ ] Write migration scripts
- [ ] Test in staging
- [ ] Migrate production tenants (phased)
- [ ] Monitor for issues
- [ ] Deprecate HMAC after migration complete

---

## References

- [NIST Guidelines on Cryptographic Key Management](https://csrc.nist.gov/publications/detail/sp/800-57-part-1/rev-5/final)
- [Azure Key Vault Documentation](https://docs.microsoft.com/azure/key-vault/)
- [AWS KMS Best Practices](https://docs.aws.amazon.com/kms/latest/developerguide/best-practices.html)
- [Python Cryptography Library](https://cryptography.io/en/latest/)
- [Ed25519 Signature Scheme](https://ed25519.cr.yp.to/)

---

## Conclusion

Asymmetric signatures provide stronger security guarantees for the decision ledger but require careful planning and implementation. The proposed phased approach allows for gradual migration with minimal disruption.

**Recommendation:** Proceed with Phase 3+ implementation after P1-P2 features are stable and in production.
