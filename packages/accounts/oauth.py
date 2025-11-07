"""OAuth social login integration for Dyocense.

Optimized for SMBs with the most popular business authentication providers:
- Google (Gmail, Google Workspace)
- Microsoft (Outlook, Microsoft 365)
- Apple (iPhone users, privacy-focused)

These three cover 95%+ of small business owners.
"""

from __future__ import annotations

import os
import secrets
from typing import Literal, Optional
from urllib.parse import urlencode

import httpx
from pydantic import BaseModel, EmailStr


OAuthProvider = Literal["google", "microsoft", "apple"]


class OAuthConfig(BaseModel):
    """OAuth provider configuration."""
    
    provider: OAuthProvider
    client_id: str
    client_secret: str
    redirect_uri: str
    scope: str
    
    @property
    def authorize_url(self) -> str:
        """Get authorization URL for provider."""
        urls = {
            "google": "https://accounts.google.com/o/oauth2/v2/auth",
            "microsoft": "https://login.microsoftonline.com/common/oauth2/v2.0/authorize",
            "apple": "https://appleid.apple.com/auth/authorize",
        }
        return urls[self.provider]
    
    @property
    def token_url(self) -> str:
        """Get token exchange URL for provider."""
        urls = {
            "google": "https://oauth2.googleapis.com/token",
            "microsoft": "https://login.microsoftonline.com/common/oauth2/v2.0/token",
            "apple": "https://appleid.apple.com/auth/token",
        }
        return urls[self.provider]
    
    @property
    def user_info_url(self) -> str:
        """Get user info URL for provider."""
        urls = {
            "google": "https://www.googleapis.com/oauth2/v2/userinfo",
            "microsoft": "https://graph.microsoft.com/v1.0/me",
            "apple": None,  # Apple returns user info in ID token
        }
        return urls[self.provider]


class OAuthUserInfo(BaseModel):
    """Standardized user information from OAuth provider."""
    
    provider: OAuthProvider
    provider_user_id: str
    email: EmailStr | None = None
    full_name: str | None = None
    picture: str | None = None
    verified_email: bool = False


class OAuthService:
    """Service for handling OAuth authentication flows."""
    
    def __init__(self):
        """Initialize OAuth service with provider configurations."""
        self.configs: dict[OAuthProvider, OAuthConfig] = {}
        self._load_configs()
    
    def _load_configs(self):
        """Load OAuth provider configurations from environment."""
        providers: list[OAuthProvider] = ["google", "microsoft", "apple"]
        
        for provider in providers:
            prefix = f"OAUTH_{provider.upper()}"
            client_id = os.getenv(f"{prefix}_CLIENT_ID")
            client_secret = os.getenv(f"{prefix}_CLIENT_SECRET")
            redirect_uri = os.getenv(f"{prefix}_REDIRECT_URI")
            
            if client_id and client_secret:
                # Default scopes per provider (optimized for SMB needs)
                default_scopes = {
                    "google": "openid email profile",  # Basic profile + email
                    "microsoft": "openid email profile User.Read",  # Microsoft 365 profile
                    "apple": "email name",  # Apple's minimal scope
                }
                
                scope = os.getenv(f"{prefix}_SCOPE", default_scopes[provider])
                
                # Default redirect URI if not specified
                if not redirect_uri:
                    base_url = os.getenv("APP_BASE_URL", "http://localhost:5173")
                    redirect_uri = f"{base_url}/auth/callback/{provider}"
                
                self.configs[provider] = OAuthConfig(
                    provider=provider,
                    client_id=client_id,
                    client_secret=client_secret,
                    redirect_uri=redirect_uri,
                    scope=scope,
                )
    
    def is_enabled(self, provider: OAuthProvider) -> bool:
        """Check if a provider is configured and enabled."""
        return provider in self.configs
    
    def get_enabled_providers(self) -> list[OAuthProvider]:
        """Get list of enabled OAuth providers."""
        return list(self.configs.keys())
    
    def get_authorization_url(self, provider: OAuthProvider, state: str | None = None) -> str:
        """Get authorization URL for initiating OAuth flow.
        
        Args:
            provider: OAuth provider name
            state: Optional state parameter for CSRF protection
            
        Returns:
            Authorization URL to redirect user to
            
        Raises:
            ValueError: If provider is not configured
        """
        if provider not in self.configs:
            raise ValueError(f"OAuth provider '{provider}' is not configured")
        
        config = self.configs[provider]
        
        # Generate state token if not provided
        if not state:
            state = secrets.token_urlsafe(32)
        
        params = {
            "client_id": config.client_id,
            "redirect_uri": config.redirect_uri,
            "response_type": "code",
            "scope": config.scope,
            "state": state,
        }
        
        # Provider-specific parameters
        if provider == "google":
            params["access_type"] = "online"
            params["prompt"] = "select_account"
        elif provider == "microsoft":
            params["response_mode"] = "query"
        
        return f"{config.authorize_url}?{urlencode(params)}"
    
    async def exchange_code_for_token(self, provider: OAuthProvider, code: str) -> str:
        """Exchange authorization code for access token.
        
        Args:
            provider: OAuth provider name
            code: Authorization code from OAuth callback
            
        Returns:
            Access token
            
        Raises:
            ValueError: If provider is not configured or token exchange fails
        """
        if provider not in self.configs:
            raise ValueError(f"OAuth provider '{provider}' is not configured")
        
        config = self.configs[provider]
        
        data = {
            "client_id": config.client_id,
            "client_secret": config.client_secret,
            "code": code,
            "redirect_uri": config.redirect_uri,
            "grant_type": "authorization_code",
        }
        
        headers = {"Accept": "application/json"}
        
        async with httpx.AsyncClient() as client:
            response = await client.post(config.token_url, data=data, headers=headers)
            
            if response.status_code != 200:
                raise ValueError(f"Token exchange failed: {response.text}")
            
            token_data = response.json()
            return token_data.get("access_token")
    
    async def get_user_info(self, provider: OAuthProvider, access_token: str) -> OAuthUserInfo:
        """Get user information from OAuth provider.
        
        Args:
            provider: OAuth provider name
            access_token: OAuth access token
            
        Returns:
            Standardized user information
            
        Raises:
            ValueError: If provider is not configured or user info fetch fails
        """
        if provider not in self.configs:
            raise ValueError(f"OAuth provider '{provider}' is not configured")
        
        config = self.configs[provider]
        
        if not config.user_info_url:
            raise ValueError(f"Provider '{provider}' does not support user info endpoint")
        
        headers = {"Authorization": f"Bearer {access_token}"}
        
        async with httpx.AsyncClient() as client:
            response = await client.get(config.user_info_url, headers=headers)
            
            if response.status_code != 200:
                raise ValueError(f"Failed to fetch user info: {response.text}")
            
            user_data = response.json()
            
            # Parse provider-specific response format
            return self._parse_user_info(provider, user_data)
    
    def _parse_user_info(self, provider: OAuthProvider, data: dict) -> OAuthUserInfo:
        """Parse provider-specific user info response into standardized format."""
        
        if provider == "google":
            return OAuthUserInfo(
                provider=provider,
                provider_user_id=data.get("id"),
                email=data.get("email"),
                full_name=data.get("name"),
                picture=data.get("picture"),
                verified_email=data.get("verified_email", False),
            )
        
        elif provider == "microsoft":
            return OAuthUserInfo(
                provider=provider,
                provider_user_id=data.get("id"),
                email=data.get("mail") or data.get("userPrincipalName"),
                full_name=data.get("displayName"),
                picture=None,  # Microsoft Graph requires separate photo endpoint
                verified_email=True,  # Microsoft accounts are verified
            )
        
        elif provider == "apple":
            return OAuthUserInfo(
                provider=provider,
                provider_user_id=data.get("sub"),
                email=data.get("email"),
                full_name=None,  # Apple provides name separately on first auth
                picture=None,
                verified_email=data.get("email_verified", False),
            )
        
        else:
            raise ValueError(f"Unknown provider: {provider}")


# Global OAuth service instance
oauth_service = OAuthService()
