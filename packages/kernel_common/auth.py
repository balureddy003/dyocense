"""Authentication and authorization with Keycloak integration and fallback."""

from __future__ import annotations

import os
import logging
from typing import Tuple, Dict, Any, Optional

logger = logging.getLogger(__name__)

try:
    from packages.accounts.repository import get_tenant_by_token, decode_jwt, get_api_token
except Exception:  # pragma: no cover - accounts package optional during bootstrap
    get_tenant_by_token = None
    decode_jwt = None
    get_api_token = None

try:
    from packages.kernel_common.keycloak_auth import KeycloakClient, KeycloakAuthFallback  # type: ignore
    from packages.kernel_common.config import get_config  # type: ignore
    _keycloak_available = True
except ImportError:
    _keycloak_available = False
    KeycloakClient = None
    KeycloakAuthFallback = None

    # Provide a minimal fallback shim when Keycloak libraries are unavailable
class _SimpleAuthFallback:
    def verify_token(self, token: str):
        # Force downstream fallbacks (internal JWT / API token / anonymous)
        raise Exception("no-keycloak")

    def health_check(self) -> dict:
        return {"status": "degraded", "mode": "fallback"}

# Ensure a callable fallback is always available
if 'KeycloakAuthFallback' in globals() and KeycloakAuthFallback is None:  # type: ignore
    KeycloakAuthFallback = _SimpleAuthFallback  # type: ignore


class AuthError(Exception):
    """Raised when authentication fails."""


# Global authentication client instance
_auth_client: Optional[Any] = None


def _get_auth_client():
    """Get or initialize authentication client (Keycloak or fallback)."""
    global _auth_client
    
    if _auth_client is not None:
        return _auth_client
    
    # Check if Keycloak should be used
    if not _keycloak_available:
        logger.warning("Keycloak libraries not available; using fallback authentication")
        _auth_client = _SimpleAuthFallback()
        return _auth_client
    
    try:
        config = get_config()
        
        # Check feature flag
        if not config.features.use_keycloak or config.features.force_inmemory:
            logger.info("Keycloak disabled by feature flag; using fallback authentication")
            _auth_client = _SimpleAuthFallback()
            return _auth_client
        
        # Try to initialize Keycloak client
        kc_config = config.keycloak
        _auth_client = KeycloakClient(
            server_url=kc_config.server_url,
            realm=kc_config.realm,
            client_id=kc_config.client_id,
            client_secret=kc_config.client_secret,
            admin_username=kc_config.admin_username,
            admin_password=kc_config.admin_password,
        )
        
        # Test connectivity
        health = _auth_client.health_check()
        if health["status"] != "healthy":
            logger.warning(
                "Keycloak health check failed; using fallback authentication. Error: %s",
                health.get("error")
            )
            _auth_client = _SimpleAuthFallback()
        else:
            logger.info("Keycloak authentication initialized successfully")
        
        return _auth_client
        
    except Exception as exc:
        logger.warning("Failed to initialize Keycloak client (%s); using fallback", exc)
        _auth_client = _SimpleAuthFallback()
        return _auth_client


def validate_bearer_token(token: str) -> Tuple[str, str]:
    """
    Validate an incoming bearer token.

    This function attempts multiple validation strategies in order:
    1. Keycloak JWT validation (production)
    2. Demo token (development fallback)
    3. Internal JWT from accounts service
    4. API token lookup
    5. Anonymous access (if enabled)

    Returns:
        Tuple of (tenant_id, subject) extracted from the token.

    Raises:
        AuthError: if the token is missing or invalid.
    """
    if not token:
        # Development convenience: allow anonymous when enabled, even with no token
        if os.getenv("ALLOW_ANONYMOUS", "false").lower() == "true":
            logger.warning("Anonymous access granted (no token)")
            return "anonymous", "anonymous"
        raise AuthError("Missing bearer token")

    # Try Keycloak/fallback authentication first
    try:
        auth_client = _get_auth_client()
        claims = auth_client.verify_token(token)
        
        tenant_id = claims.get("tenant_id") or claims.get("azp") or claims.get("aud")
        subject = claims.get("sub") or claims.get("preferred_username") or "user"
        
        if tenant_id:
            return tenant_id, subject
    except Exception as exc:
        logger.debug("Keycloak token validation failed: %s", exc)
        # Fall through to other validation methods

    # Fallback: Internal JWT from accounts service
    if decode_jwt and token.count(".") == 2:
        payload = decode_jwt(token)
        if payload:
            tenant_id = payload.get("tenant_id")
            subject = payload.get("sub") or payload.get("user_id") or "user"
            if tenant_id:
                logger.debug("Validated internal JWT token")
                return tenant_id, subject

    # Fallback: API token lookup in database
    if get_tenant_by_token:
        tenant = get_tenant_by_token(token)
        if tenant:
            logger.debug("Validated API token from tenant lookup")
            return tenant.tenant_id, "api-key"
    
    if get_api_token:
        record = get_api_token(token)
        if record:
            logger.debug("Validated API token from token lookup")
            return record.tenant_id, record.user_id or "api-key"

    # Fallback: Anonymous access (development only)
    if os.getenv("ALLOW_ANONYMOUS", "false").lower() == "true":
        logger.warning("Anonymous access granted (not for production)")
        return "anonymous", "anonymous"

    raise AuthError("Invalid bearer token")


def get_auth_health() -> Dict[str, Any]:
    """Get authentication system health status."""
    try:
        auth_client = _get_auth_client()
        return auth_client.health_check()
    except Exception as exc:
        return {
            "status": "error",
            "error": str(exc)
        }


__all__ = ["AuthError", "validate_bearer_token", "get_auth_health"]
