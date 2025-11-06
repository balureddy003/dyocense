"""Keycloak authentication and authorization implementation.

This module provides JWT token validation, user management, and realm operations
using Keycloak as the identity provider.
"""

from __future__ import annotations

import logging
from typing import Optional, Dict, Any
import requests
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class KeycloakClient:
    """Client for Keycloak authentication and user management."""
    
    def __init__(
        self, 
        server_url: str,
        realm: str,
        client_id: str,
        client_secret: Optional[str] = None,
        admin_username: Optional[str] = None,
        admin_password: Optional[str] = None
    ):
        self.server_url = server_url.rstrip("/")
        self.realm = realm
        self.client_id = client_id
        self.client_secret = client_secret
        self.admin_username = admin_username
        self.admin_password = admin_password
        
        self._admin_token: Optional[str] = None
        self._admin_token_expires: Optional[datetime] = None
        self._public_key: Optional[str] = None
    
    def _get_realm_url(self, path: str = "") -> str:
        """Construct URL for realm-specific endpoint."""
        return f"{self.server_url}/realms/{self.realm}{path}"
    
    def _get_admin_url(self, path: str = "") -> str:
        """Construct URL for admin API endpoint."""
        return f"{self.server_url}/admin/realms/{self.realm}{path}"
    
    def _get_admin_token(self) -> str:
        """Get admin access token with automatic refresh."""
        if (
            self._admin_token 
            and self._admin_token_expires 
            and datetime.utcnow() < self._admin_token_expires
        ):
            return self._admin_token
        
        if not self.admin_username or not self.admin_password:
            raise ValueError("Admin credentials not configured")
        
        url = f"{self.server_url}/realms/master/protocol/openid-connect/token"
        data = {
            "grant_type": "password",
            "client_id": "admin-cli",
            "username": self.admin_username,
            "password": self.admin_password,
        }
        
        response = requests.post(url, data=data, timeout=5)
        response.raise_for_status()
        
        token_data = response.json()
        self._admin_token = token_data["access_token"]
        expires_in = token_data.get("expires_in", 300)
        self._admin_token_expires = datetime.utcnow() + timedelta(seconds=expires_in - 30)
        
        return self._admin_token
    
    def get_public_key(self) -> str:
        """Fetch realm public key for JWT signature verification."""
        if self._public_key:
            return self._public_key
        
        url = self._get_realm_url()
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        
        realm_data = response.json()
        self._public_key = realm_data["public_key"]
        return self._public_key
    
    def verify_token(self, token: str) -> Dict[str, Any]:
        """Verify JWT token and extract claims.
        
        Args:
            token: JWT access token
        
        Returns:
            Dictionary of token claims (sub, tenant_id, email, etc.)
        
        Raises:
            ValueError: If token is invalid or expired
        """
        try:
            import jwt
            from jwt import PyJWKClient
        except ImportError:
            raise ImportError("PyJWT required for token verification. Install: pip install pyjwt cryptography")
        
        # Get JWKS URL for key verification
        jwks_url = self._get_realm_url("/protocol/openid-connect/certs")
        jwks_client = PyJWKClient(jwks_url, timeout=5)
        
        try:
            signing_key = jwks_client.get_signing_key_from_jwt(token)
            
            # Verify and decode token
            claims = jwt.decode(
                token,
                signing_key.key,
                algorithms=["RS256"],
                audience=self.client_id,
                options={
                    "verify_signature": True,
                    "verify_exp": True,
                    "verify_aud": True,
                }
            )
            
            return claims
            
        except jwt.ExpiredSignatureError:
            raise ValueError("Token has expired")
        except jwt.InvalidTokenError as exc:
            raise ValueError(f"Invalid token: {exc}")
    
    def create_user(
        self, 
        username: str, 
        email: str, 
        password: str,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        attributes: Optional[Dict[str, Any]] = None
    ) -> str:
        """Create a new user in Keycloak.
        
        Args:
            username: Username for login
            email: User email address
            password: Initial password
            first_name: User first name
            last_name: User last name
            attributes: Custom attributes (e.g., tenant_id)
        
        Returns:
            User ID (UUID)
        """
        admin_token = self._get_admin_token()
        url = self._get_admin_url("/users")
        
        user_data = {
            "username": username,
            "email": email,
            "enabled": True,
            "emailVerified": False,
            "credentials": [
                {
                    "type": "password",
                    "value": password,
                    "temporary": False
                }
            ]
        }
        
        if first_name:
            user_data["firstName"] = first_name
        if last_name:
            user_data["lastName"] = last_name
        if attributes:
            user_data["attributes"] = attributes
        
        headers = {
            "Authorization": f"Bearer {admin_token}",
            "Content-Type": "application/json"
        }
        
        response = requests.post(url, json=user_data, headers=headers, timeout=5)
        response.raise_for_status()
        
        # Extract user ID from Location header
        location = response.headers.get("Location", "")
        user_id = location.split("/")[-1]
        
        logger.info("Created Keycloak user: %s (ID: %s)", username, user_id)
        return user_id
    
    def create_realm(self, tenant_id: str, display_name: str) -> None:
        """Create a new realm for tenant isolation.
        
        Args:
            tenant_id: Unique tenant identifier
            display_name: Human-readable realm name
        """
        admin_token = self._get_admin_token()
        url = f"{self.server_url}/admin/realms"
        
        realm_data = {
            "realm": tenant_id,
            "displayName": display_name,
            "enabled": True,
            "sslRequired": "external",
            "registrationAllowed": False,
            "loginWithEmailAllowed": True,
            "duplicateEmailsAllowed": False,
            "resetPasswordAllowed": True,
            "editUsernameAllowed": False,
            "bruteForceProtected": True,
        }
        
        headers = {
            "Authorization": f"Bearer {admin_token}",
            "Content-Type": "application/json"
        }
        
        response = requests.post(url, json=realm_data, headers=headers, timeout=5)
        response.raise_for_status()
        
        logger.info("Created Keycloak realm: %s (%s)", tenant_id, display_name)
    
    def health_check(self) -> Dict[str, Any]:
        """Check Keycloak server health and connectivity.
        
        Returns:
            Health status dictionary
        """
        try:
            url = self._get_realm_url()
            response = requests.get(url, timeout=2)
            response.raise_for_status()
            
            return {
                "status": "healthy",
                "server_url": self.server_url,
                "realm": self.realm,
                "reachable": True
            }
        except Exception as exc:
            return {
                "status": "unhealthy",
                "server_url": self.server_url,
                "realm": self.realm,
                "reachable": False,
                "error": str(exc)
            }


class KeycloakAuthFallback:
    """Fallback authentication for development when Keycloak unavailable."""
    
    def verify_token(self, token: str) -> Dict[str, Any]:
        """Accept demo tokens for development."""
        if token.startswith("demo-"):
            tenant_id = token
            return {
                "sub": "stub-user",
                "tenant_id": tenant_id,
                "email": "stub@example.com",
                "preferred_username": "stub-user",
                "mode": "fallback"
            }
        raise ValueError("Invalid token format for fallback mode")
    
    def create_user(self, *args, **kwargs) -> str:
        """No-op user creation in fallback mode."""
        logger.warning("User creation skipped in fallback auth mode")
        return "fallback-user-id"
    
    def create_realm(self, *args, **kwargs) -> None:
        """No-op realm creation in fallback mode."""
        logger.warning("Realm creation skipped in fallback auth mode")
    
    def health_check(self) -> Dict[str, Any]:
        """Report fallback mode status."""
        return {
            "status": "degraded",
            "mode": "fallback",
            "message": "Using demo token authentication; not suitable for production"
        }


__all__ = ["KeycloakClient", "KeycloakAuthFallback"]
