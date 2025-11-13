-- Phase 3: Add per-tenant signing keys and ledger signature metadata

CREATE SCHEMA IF NOT EXISTS tenants;

-- Create signing_keys table if not exists
CREATE TABLE IF NOT EXISTS tenants.signing_keys (
    id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL,
    algorithm TEXT NOT NULL, -- 'ed25519', 'rsa-2048', etc
    public_key TEXT, -- PEM
    key_vault_ref TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMPTZ,
    revoked_at TIMESTAMPTZ,
    status TEXT NOT NULL DEFAULT 'active'
);

CREATE INDEX IF NOT EXISTS idx_signing_keys_tenant ON tenants.signing_keys (tenant_id);

CREATE INDEX IF NOT EXISTS idx_signing_keys_status ON tenants.signing_keys (status);

-- Augment decision_ledger with signature metadata columns
ALTER TABLE tenants.decision_ledger
ADD COLUMN IF NOT EXISTS signing_key_id TEXT,
ADD COLUMN IF NOT EXISTS signature_algorithm TEXT,
ADD COLUMN IF NOT EXISTS signature_version INT;