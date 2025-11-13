# Phase 3 Implementation Log (Micro-Seasonality + Asymmetric Signatures)

Date: 2025-11-12

## Overview

Phase 3 expands analytics with micro-seasonality detection and upgrades the decision ledger security model to support asymmetric signatures while preserving HMAC compatibility.

## Micro-Seasonality

- Module: `services/smb_gateway/micro_seasonality.py`
- Flag: `ENABLE_MICRO_SEASONALITY` (1/true/yes)
- Endpoint: `POST /v1/tenants/{tenant_id}/analytics/detect-seasonality`
- Notes:
  - Uses `statsmodels` seasonal_decompose with candidate periods (e.g., 24, 168)
  - Graceful degradation if optional deps missing
  - Returns patterns, strength, recommended periods

## Asymmetric Signatures (Signing Keys)

- Package: `services/smb_gateway/signing_keys/`
  - `models.py`: `KeyAlgorithm`, `SigningKey`
  - `key_manager.py`: dual-mode signing helpers, key management
  - `__init__.py`: exports & flags
- Flags:
  - `ENABLE_ASYMMETRIC_SIGNING`: gate asymmetric usage (default: off)
  - `DEFAULT_SIGNATURE_MODE`: `auto|hmac|asymmetric` (dev default: hmac)
  - `ED25519_PRIVATE_KEY_PEM`: optional dev-only private key for local signing
- Ledger integration: `services/smb_gateway/decision_ledger_pg.py`
  - Adds `signing_key_id`, `signature_algorithm`, `signature_version` columns
  - Signs via asymmetric if available; falls back to HMAC
  - Verifies mixed entries (asymmetric preferred; HMAC fallback)
- Database migration:
  - `infra/postgres/migrations/20251112_add_signing_keys.sql`
  - Creates `tenants.signing_keys` and augments `tenants.decision_ledger`

## Admin APIs for Key Management

- Endpoints (gated by `ENABLE_ASYMMETRIC_SIGNING`):
  - `GET  /v1/tenants/{tenant_id}/security/keys` — list keys
  - `POST /v1/tenants/{tenant_id}/security/keys` — register public key (PEM)
  - `POST /v1/tenants/{tenant_id}/security/keys/{key_id}/activate` — make active
  - `POST /v1/tenants/{tenant_id}/security/keys/{key_id}/revoke` — revoke
  - `POST /v1/tenants/{tenant_id}/security/rotate` — expire current and add new

## Dev Enable/Disable Behavior

- Dev defaults to HMAC only (`ENV=dev` => DEFAULT_SIGNATURE_MODE=hmac)
- To try asymmetric in dev:
  - `export ENABLE_ASYMMETRIC_SIGNING=1`
  - `export DEFAULT_SIGNATURE_MODE=auto` (or `asymmetric`)
  - Register a tenant's public key via the admin API
  - Optionally set `ED25519_PRIVATE_KEY_PEM` for local signing

## Validation

- Static checks: No errors in modified files
- Backward compatibility: HMAC remains default in dev; auto enables asymmetric if tenant has a key

## Next Steps

- Add integration tests for dual-mode sign/verify
- Optional: Admin auth for key endpoints (RBAC)
- Optional: Tenant-scoped settings to override signature mode
- KMS/Key Vault integration for production-grade private key operations
- Observability: metrics for sign/verify paths and failure alerts
