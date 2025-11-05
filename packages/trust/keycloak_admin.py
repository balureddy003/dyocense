"""Keycloak Admin API client for tenant and user management.

This module provides a wrapper around the Keycloak Admin API to:
- Create realms per tenant
- Manage realm users and credentials
- Handle authentication flows
"""

from __future__ import annotations

import os
import secrets
import string
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)

try:
    from keycloak import KeycloakAdmin
    from keycloak.exceptions import KeycloakError
    KEYCLOAK_AVAILABLE = True
except ImportError:
    KEYCLOAK_AVAILABLE = False
    KeycloakAdmin = None
    KeycloakError = Exception


class KeycloakAdminClient:
    """Client for Keycloak Admin API operations."""

    def __init__(
        self,
        server_url: Optional[str] = None,
        realm_name: str = "master",
        client_id: str = "admin-cli",
        client_secret: Optional[str] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
    ):
        """Initialize Keycloak Admin Client.

        Args:
            server_url: Keycloak server URL (default from KEYCLOAK_SERVER_URL env var)
            realm_name: Realm to authenticate against (default: "master")
            client_id: Client ID for authentication (default: "admin-cli")
            client_secret: Client secret for service account
            username: Username for password flow
            password: Password for password flow

        Raises:
            RuntimeError: If Keycloak is not available or connection fails
        """
        if not KEYCLOAK_AVAILABLE:
            raise RuntimeError(
                "python-keycloak is not installed. Install it with: pip install python-keycloak"
            )

        self.server_url = server_url or os.getenv("KEYCLOAK_SERVER_URL", "http://localhost:8080")
        self.realm_name = realm_name
        self.client_id = client_id

        try:
            if client_secret:
                # Service account flow
                self.admin = KeycloakAdmin(
                    server_url=self.server_url,
                    realm_name=realm_name,
                    client_id=client_id,
                    client_secret=client_secret,
                    verify=True,
                )
            elif username and password:
                # Password flow
                self.admin = KeycloakAdmin(
                    server_url=self.server_url,
                    realm_name=realm_name,
                    client_id=client_id,
                    username=username,
                    password=password,
                    verify=True,
                )
            else:
                raise ValueError(
                    "Either client_secret or (username, password) must be provided"
                )
            logger.info(f"Connected to Keycloak at {self.server_url}")
        except KeycloakError as e:
            logger.error(f"Failed to connect to Keycloak: {e}")
            raise RuntimeError(f"Keycloak connection failed: {e}")

    def create_realm(self, realm_id: str, display_name: str) -> Dict[str, Any]:
        """Create a new realm for a tenant.

        Args:
            realm_id: Unique identifier for the realm (lowercase, no spaces)
            display_name: Display name for the realm

        Returns:
            Realm creation response

        Raises:
            KeycloakError: If realm creation fails
        """
        try:
            # Check if realm already exists
            existing_realms = self.admin.get_realms()
            if any(r["realm"] == realm_id for r in existing_realms):
                logger.info(f"Realm {realm_id} already exists")
                return {"realm": realm_id, "status": "already_exists"}

            # Create realm
            payload = {
                "realm": realm_id,
                "displayName": display_name,
                "enabled": True,
                "accessTokenLifespan": 3600,  # 1 hour
                "refreshTokenMaxReuse": 0,
                "actionTokenGeneratedByAdminLifespan": 604800,  # 7 days
                "sslRequired": "external",
            }

            self.admin.create_realm(payload)
            logger.info(f"Created realm: {realm_id}")
            return {"realm": realm_id, "status": "created"}
        except KeycloakError as e:
            logger.error(f"Failed to create realm {realm_id}: {e}")
            raise

    def delete_realm(self, realm_id: str) -> bool:
        """Delete a realm (useful for deprovisioning).

        Args:
            realm_id: Realm identifier

        Returns:
            True if successful

        Raises:
            KeycloakError: If deletion fails
        """
        try:
            self.admin.realm_name = realm_id
            self.admin.delete_realm(realm_id)
            logger.info(f"Deleted realm: {realm_id}")
            return True
        except KeycloakError as e:
            logger.error(f"Failed to delete realm {realm_id}: {e}")
            raise

    def create_user(
        self,
        realm_id: str,
        email: str,
        username: Optional[str] = None,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        temporary_password: bool = True,
    ) -> Dict[str, Any]:
        """Create a user in a realm.

        Args:
            realm_id: Realm identifier
            email: User's email address
            username: Username (defaults to email prefix)
            first_name: User's first name
            last_name: User's last name
            temporary_password: If True, generates a temporary password and requires reset on first login

        Returns:
            User creation response with user ID and temporary password

        Raises:
            KeycloakError: If user creation fails
        """
        try:
            if username is None:
                username = email.split("@")[0]

            # Switch to the target realm
            old_realm = self.admin.realm_name
            self.admin.realm_name = realm_id

            # Check if user already exists
            existing_users = self.admin.get_users({"username": username})
            if existing_users:
                logger.info(f"User {username} already exists in realm {realm_id}")
                self.admin.realm_name = old_realm
                return {"username": username, "email": email, "status": "already_exists"}

            # Generate temporary password
            temp_password = self._generate_password()

            # Create user payload
            user_payload = {
                "username": username,
                "email": email,
                "emailVerified": True,
                "firstName": first_name or "",
                "lastName": last_name or "",
                "enabled": True,
                "credentials": [
                    {
                        "type": "password",
                        "value": temp_password,
                        "temporary": temporary_password,
                    }
                ],
            }

            # Create user
            user_id = self.admin.create_user(user_payload)
            logger.info(f"Created user {username} in realm {realm_id}: {user_id}")

            self.admin.realm_name = old_realm
            return {
                "user_id": user_id,
                "username": username,
                "email": email,
                "temporary_password": temp_password,
                "status": "created",
            }
        except KeycloakError as e:
            logger.error(f"Failed to create user {email} in realm {realm_id}: {e}")
            self.admin.realm_name = old_realm
            raise

    def reset_user_password(
        self, realm_id: str, user_id: str, temporary: bool = False
    ) -> str:
        """Reset a user's password.

        Args:
            realm_id: Realm identifier
            user_id: User ID
            temporary: If True, user must change password on next login

        Returns:
            New temporary password

        Raises:
            KeycloakError: If password reset fails
        """
        try:
            old_realm = self.admin.realm_name
            self.admin.realm_name = realm_id

            new_password = self._generate_password()

            # Set new password
            self.admin.set_user_password(user_id, new_password, temporary=temporary)

            logger.info(f"Reset password for user {user_id} in realm {realm_id}")
            self.admin.realm_name = old_realm
            return new_password
        except KeycloakError as e:
            logger.error(f"Failed to reset password for user {user_id}: {e}")
            self.admin.realm_name = old_realm
            raise

    def get_user(self, realm_id: str, user_id: str) -> Dict[str, Any]:
        """Get user details.

        Args:
            realm_id: Realm identifier
            user_id: User ID

        Returns:
            User details

        Raises:
            KeycloakError: If user not found
        """
        try:
            old_realm = self.admin.realm_name
            self.admin.realm_name = realm_id

            user = self.admin.get_user(user_id)

            self.admin.realm_name = old_realm
            return user
        except KeycloakError as e:
            logger.error(f"Failed to get user {user_id} from realm {realm_id}: {e}")
            self.admin.realm_name = old_realm
            raise

    def delete_user(self, realm_id: str, user_id: str) -> bool:
        """Delete a user from a realm.

        Args:
            realm_id: Realm identifier
            user_id: User ID

        Returns:
            True if successful

        Raises:
            KeycloakError: If deletion fails
        """
        try:
            old_realm = self.admin.realm_name
            self.admin.realm_name = realm_id

            self.admin.delete_user(user_id)

            logger.info(f"Deleted user {user_id} from realm {realm_id}")
            self.admin.realm_name = old_realm
            return True
        except KeycloakError as e:
            logger.error(f"Failed to delete user {user_id} from realm {realm_id}: {e}")
            self.admin.realm_name = old_realm
            raise

    def create_client(self, realm_id: str, client_id: str, **kwargs) -> Dict[str, Any]:
        """Create an OAuth2 client in a realm.

        Args:
            realm_id: Realm identifier
            client_id: Client ID
            **kwargs: Additional client configuration

        Returns:
            Client creation response

        Raises:
            KeycloakError: If client creation fails
        """
        try:
            old_realm = self.admin.realm_name
            self.admin.realm_name = realm_id

            client_payload = {
                "clientId": client_id,
                "name": kwargs.get("name", client_id),
                "enabled": True,
                "redirectUris": kwargs.get("redirectUris", ["http://localhost:3000/*"]),
                "webOrigins": kwargs.get("webOrigins", ["http://localhost:3000"]),
                "publicClient": kwargs.get("publicClient", True),
                "directAccessGrantsEnabled": True,
            }

            resp = self.admin.create_client(client_payload)
            logger.info(f"Created client {client_id} in realm {realm_id}")

            self.admin.realm_name = old_realm
            return resp
        except KeycloakError as e:
            logger.error(f"Failed to create client {client_id} in realm {realm_id}: {e}")
            self.admin.realm_name = old_realm
            raise

    @staticmethod
    def _generate_password(length: int = 12) -> str:
        """Generate a random password.

        Args:
            length: Password length (default: 12)

        Returns:
            Random password with mix of upper, lower, digits, and special chars
        """
        chars = string.ascii_uppercase + string.ascii_lowercase + string.digits + "!@#$%"
        password = "".join(secrets.choice(chars) for _ in range(length))
        return password

    @staticmethod
    def is_available() -> bool:
        """Check if Keycloak client is available."""
        return KEYCLOAK_AVAILABLE


__all__ = ["KeycloakAdminClient"]
