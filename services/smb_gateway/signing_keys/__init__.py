"""
Signing keys management (Phase 3 scaffolding)

- Provides dual-mode signature control: HMAC (legacy) and Ed25519 (asymmetric)
- Dev-friendly toggles via environment variables

Environment flags:
- DEFAULT_SIGNATURE_MODE: 'auto' | 'hmac' | 'asymmetric' (default: 'hmac' in dev, 'auto' otherwise)
- ENABLE_ASYMMETRIC_SIGNING: '1'/'true' to allow asymmetric usage
- ED25519_PRIVATE_KEY_PEM: optional PEM for dev signing (when asymmetric enabled)

This module is intentionally lightweight and safe to import if cryptography is missing
(it will gracefully fall back to HMAC-only).
"""
from .models import KeyAlgorithm, SigningKey
from .key_manager import (
    DEFAULT_SIGNATURE_MODE,
    ENABLE_ASYMMETRIC_SIGNING,
    tenant_has_signing_key,
    get_active_signing_key,
    sign_entry_auto,
    verify_entry_signature,
)

__all__ = [
    "KeyAlgorithm",
    "SigningKey",
    "DEFAULT_SIGNATURE_MODE",
    "ENABLE_ASYMMETRIC_SIGNING",
    "tenant_has_signing_key",
    "get_active_signing_key",
    "sign_entry_auto",
    "verify_entry_signature",
]
