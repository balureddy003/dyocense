"""Tenant onboarding service coordinating Keycloak and MongoDB operations."""

from __future__ import annotations

import logging
from typing import Optional, Dict, Any
from datetime import datetime

from packages.trust.keycloak_admin import KeycloakAdminClient

logger = logging.getLogger(__name__)


class TenantOnboardingService:
    """Service for onboarding new tenants with Keycloak realm and initial user."""

    def __init__(
        self,
        keycloak_client: Optional[KeycloakAdminClient] = None,
        server_url: Optional[str] = None,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
    ):
        """Initialize onboarding service.

        Args:
            keycloak_client: Optional KeycloakAdminClient instance. If provided, other args are ignored.
            server_url: Keycloak server URL
            client_id: Keycloak client ID
            client_secret: Client secret for service account
            username: Username for password flow
            password: Password for password flow
        """
        self.keycloak = keycloak_client
        if self.keycloak is None and KeycloakAdminClient.is_available():
            try:
                self.keycloak = KeycloakAdminClient(
                    server_url=server_url,
                    client_id=client_id,
                    client_secret=client_secret,
                    username=username,
                    password=password,
                )
            except Exception as e:
                logger.warning(f"Failed to initialize Keycloak client: {e}. Proceeding without Keycloak.")

    def onboard_tenant(
        self,
        tenant_id: str,
        tenant_name: str,
        owner_email: str,
        owner_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Onboard a new tenant with Keycloak realm and initial user.

        Args:
            tenant_id: Unique tenant identifier (from MongoDB)
            tenant_name: Display name for the tenant
            owner_email: Owner's email address
            owner_name: Owner's full name (optional)

        Returns:
            Onboarding result containing realm info and user credentials

        Raises:
            ValueError: If required parameters are invalid
            RuntimeError: If onboarding fails
        """
        logger.info(f"Starting onboarding for tenant {tenant_id}")

        # Validate inputs
        if not tenant_id or not tenant_name or not owner_email:
            raise ValueError("tenant_id, tenant_name, and owner_email are required")

        if not self.keycloak:
            logger.warning("Keycloak not available, skipping realm provisioning")
            return self._fallback_onboarding_response(tenant_id, owner_email)

        try:
            # Create realm
            realm_id = self._sanitize_realm_id(tenant_id)
            realm_result = self.keycloak.create_realm(realm_id, tenant_name)
            logger.info(f"Realm creation result: {realm_result}")

            # Create OAuth2 client for the UI
            try:
                client_result = self.keycloak.create_client(
                    realm_id,
                    "dyocense-ui",
                    name="Dyocense UI",
                    redirectUris=[
                        "http://localhost:3000/*",
                        "http://localhost:5173/*",
                        "https://dyocense.io/*",
                    ],
                    webOrigins=["*"],
                )
                logger.info(f"OAuth2 client created: {client_result}")
            except Exception as e:
                logger.warning(f"Failed to create OAuth2 client, continuing: {e}")

            # Create initial user
            first_name, last_name = self._parse_name(owner_name)
            user_result = self.keycloak.create_user(
                realm_id,
                owner_email,
                username=owner_email.split("@")[0],
                first_name=first_name,
                last_name=last_name,
                temporary_password=True,
            )
            logger.info(f"User created: {user_result.get('user_id')}")

            return {
                "status": "success",
                "tenant_id": tenant_id,
                "realm_id": realm_id,
                "user_id": user_result.get("user_id"),
                "username": user_result.get("username"),
                "email": user_result.get("email"),
                "temporary_password": user_result.get("temporary_password"),
                "keycloak_url": self.keycloak.server_url,
                "login_url": f"{self.keycloak.server_url}/auth/realms/{realm_id}/protocol/openid-connect/auth",
                "timestamp": datetime.utcnow().isoformat(),
            }
        except Exception as e:
            logger.error(f"Tenant onboarding failed: {e}")
            raise RuntimeError(f"Failed to onboard tenant {tenant_id}: {str(e)}")

    def deprovisioning_tenant(self, tenant_id: str) -> bool:
        """Deprovision a tenant (delete realm and all related data).

        Args:
            tenant_id: Tenant identifier

        Returns:
            True if successful

        Raises:
            RuntimeError: If deprovisioning fails
        """
        logger.info(f"Starting deprovisioning for tenant {tenant_id}")

        if not self.keycloak:
            logger.warning("Keycloak not available, skipping realm deletion")
            return True

        try:
            realm_id = self._sanitize_realm_id(tenant_id)
            self.keycloak.delete_realm(realm_id)
            logger.info(f"Successfully deprovisioned tenant {tenant_id}")
            return True
        except Exception as e:
            logger.error(f"Tenant deprovisioning failed: {e}")
            raise RuntimeError(f"Failed to deprovision tenant {tenant_id}: {str(e)}")

    @staticmethod
    def _sanitize_realm_id(tenant_id: str) -> str:
        """Convert tenant ID to valid Keycloak realm ID.

        Keycloak realm names must be lowercase, alphanumeric, and use hyphens.

        Args:
            tenant_id: Raw tenant identifier

        Returns:
            Sanitized realm ID
        """
        # Convert to lowercase and replace underscores/spaces with hyphens
        realm_id = tenant_id.lower().replace("_", "-").replace(" ", "-")
        # Remove special characters except hyphens
        realm_id = "".join(c for c in realm_id if c.isalnum() or c == "-")
        # Remove leading/trailing hyphens
        realm_id = realm_id.strip("-")
        return realm_id or "realm"

    @staticmethod
    def _parse_name(full_name: Optional[str]) -> tuple[str, str]:
        """Parse full name into first and last name.

        Args:
            full_name: Full name string

        Returns:
            Tuple of (first_name, last_name)
        """
        if not full_name:
            return "", ""

        parts = full_name.strip().split(maxsplit=1)
        first_name = parts[0] if parts else ""
        last_name = parts[1] if len(parts) > 1 else ""
        return first_name, last_name

    @staticmethod
    def _fallback_onboarding_response(tenant_id: str, owner_email: str) -> Dict[str, Any]:
        """Generate fallback response when Keycloak is not available.

        Args:
            tenant_id: Tenant identifier
            owner_email: Owner's email

        Returns:
            Fallback response
        """
        return {
            "status": "success_without_keycloak",
            "tenant_id": tenant_id,
            "realm_id": None,
            "user_id": None,
            "email": owner_email,
            "message": "Tenant created but Keycloak is not available. Manual setup required.",
            "timestamp": datetime.utcnow().isoformat(),
        }


__all__ = ["TenantOnboardingService"]
