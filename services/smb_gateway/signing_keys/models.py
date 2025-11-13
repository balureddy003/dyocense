from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class KeyAlgorithm(str, Enum):
    hmac_sha256 = "hmac-sha256"
    ed25519 = "ed25519"
    rsa_2048 = "rsa-2048"
    rsa_4096 = "rsa-4096"


@dataclass
class SigningKey:
    id: str
    tenant_id: str
    algorithm: KeyAlgorithm
    public_key_pem: Optional[str] = None
    key_vault_ref: Optional[str] = None
    status: str = "active"  # active | expired | revoked
