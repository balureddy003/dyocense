"""Connector testing and validation."""

import logging
from typing import Any
import httpx

from .models import ConnectorTestResult

logger = logging.getLogger(__name__)


class ConnectorTester:
    """Test connector configurations to ensure they work."""
    
    async def test_connector(
        self,
        connector_type: str,
        config: dict[str, Any]
    ) -> ConnectorTestResult:
        """
        Test a connector configuration.
        
        Args:
            connector_type: Type of connector (e.g., "xero", "google-drive")
            config: Configuration dict with credentials
            
        Returns:
            ConnectorTestResult with success status and message
        """
        try:
            if connector_type == "google-drive":
                return await self._test_google_drive(config)
            elif connector_type == "xero":
                return await self._test_xero(config)
            elif connector_type == "shopify":
                return await self._test_shopify(config)
            elif connector_type == "square":
                return await self._test_square(config)
            elif connector_type == "stripe":
                return await self._test_stripe(config)
            elif connector_type == "rest-api":
                return await self._test_rest_api(config)
            elif connector_type == "postgres":
                return await self._test_postgres(config)
            elif connector_type in {"csv_upload", "csv", "manual_upload"}:
                return ConnectorTestResult(
                    success=True,
                    message="CSV uploads are manual sources. No live connection required.",
                    details={"requires_manual_upload": True}
                )
            else:
                return ConnectorTestResult(
                    success=False,
                    message=f"Connector type '{connector_type}' not supported yet",
                    error_code="UNSUPPORTED_TYPE"
                )
        except Exception as e:
            logger.error(f"Connector test failed: {e}")
            return ConnectorTestResult(
                success=False,
                message=f"Test failed: {str(e)}",
                error_code="TEST_FAILED"
            )
    
    async def _test_google_drive(self, config: dict) -> ConnectorTestResult:
        """Test Google Drive connection (requires OAuth token)."""
        # For OAuth, we expect an access_token
        access_token = config.get("access_token")
        
        if not access_token:
            return ConnectorTestResult(
                success=False,
                message="Google Drive requires OAuth authentication. Please complete OAuth flow.",
                error_code="OAUTH_REQUIRED"
            )
        
        # Test by fetching user info
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    "https://www.googleapis.com/drive/v3/about?fields=user",
                    headers={"Authorization": f"Bearer {access_token}"},
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    user_email = data.get("user", {}).get("emailAddress", "Unknown")
                    return ConnectorTestResult(
                        success=True,
                        message=f"Successfully connected to Google Drive for {user_email}",
                        details={"email": user_email}
                    )
                elif response.status_code == 401:
                    return ConnectorTestResult(
                        success=False,
                        message="Invalid or expired OAuth token. Please re-authenticate.",
                        error_code="INVALID_TOKEN"
                    )
                else:
                    return ConnectorTestResult(
                        success=False,
                        message=f"Failed to connect: HTTP {response.status_code}",
                        error_code="CONNECTION_FAILED"
                    )
        except Exception as e:
            return ConnectorTestResult(
                success=False,
                message=f"Connection error: {str(e)}",
                error_code="NETWORK_ERROR"
            )
    
    async def _test_xero(self, config: dict) -> ConnectorTestResult:
        """Test Xero connection (OAuth)."""
        access_token = config.get("access_token")
        
        if not access_token:
            return ConnectorTestResult(
                success=False,
                message="Xero requires OAuth authentication. Please complete OAuth flow.",
                error_code="OAUTH_REQUIRED"
            )
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    "https://api.xero.com/api.xro/2.0/Organisation",
                    headers={"Authorization": f"Bearer {access_token}"},
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    org_name = data.get("Organisations", [{}])[0].get("Name", "Unknown")
                    return ConnectorTestResult(
                        success=True,
                        message=f"Successfully connected to Xero: {org_name}",
                        details={"organization": org_name}
                    )
                elif response.status_code == 401:
                    return ConnectorTestResult(
                        success=False,
                        message="Invalid or expired OAuth token. Please re-authenticate.",
                        error_code="INVALID_TOKEN"
                    )
                else:
                    return ConnectorTestResult(
                        success=False,
                        message=f"Failed to connect: HTTP {response.status_code}",
                        error_code="CONNECTION_FAILED"
                    )
        except Exception as e:
            return ConnectorTestResult(
                success=False,
                message=f"Connection error: {str(e)}",
                error_code="NETWORK_ERROR"
            )
    
    async def _test_shopify(self, config: dict) -> ConnectorTestResult:
        """Test Shopify connection."""
        shop_url = config.get("shop_url", "").rstrip("/")
        access_token = config.get("access_token") or config.get("api_key")
        
        if not shop_url or not access_token:
            return ConnectorTestResult(
                success=False,
                message="Shopify requires shop URL and access token",
                error_code="MISSING_CREDENTIALS"
            )
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{shop_url}/admin/api/2024-01/shop.json",
                    headers={"X-Shopify-Access-Token": access_token},
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    shop_name = data.get("shop", {}).get("name", "Unknown")
                    return ConnectorTestResult(
                        success=True,
                        message=f"Successfully connected to Shopify: {shop_name}",
                        details={"shop": shop_name}
                    )
                elif response.status_code == 401:
                    return ConnectorTestResult(
                        success=False,
                        message="Invalid access token",
                        error_code="INVALID_TOKEN"
                    )
                else:
                    return ConnectorTestResult(
                        success=False,
                        message=f"Failed to connect: HTTP {response.status_code}",
                        error_code="CONNECTION_FAILED"
                    )
        except Exception as e:
            return ConnectorTestResult(
                success=False,
                message=f"Connection error: {str(e)}",
                error_code="NETWORK_ERROR"
            )
    
    async def _test_square(self, config: dict) -> ConnectorTestResult:
        """Test Square connection."""
        access_token = config.get("access_token")
        
        if not access_token:
            return ConnectorTestResult(
                success=False,
                message="Square requires an access token",
                error_code="MISSING_CREDENTIALS"
            )
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    "https://connect.squareup.com/v2/locations",
                    headers={"Authorization": f"Bearer {access_token}"},
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    locations = data.get("locations", [])
                    return ConnectorTestResult(
                        success=True,
                        message=f"Successfully connected to Square ({len(locations)} location(s))",
                        details={"locations": len(locations)}
                    )
                elif response.status_code == 401:
                    return ConnectorTestResult(
                        success=False,
                        message="Invalid access token",
                        error_code="INVALID_TOKEN"
                    )
                else:
                    return ConnectorTestResult(
                        success=False,
                        message=f"Failed to connect: HTTP {response.status_code}",
                        error_code="CONNECTION_FAILED"
                    )
        except Exception as e:
            return ConnectorTestResult(
                success=False,
                message=f"Connection error: {str(e)}",
                error_code="NETWORK_ERROR"
            )
    
    async def _test_stripe(self, config: dict) -> ConnectorTestResult:
        """Test Stripe connection."""
        api_key = config.get("api_key")
        
        if not api_key:
            return ConnectorTestResult(
                success=False,
                message="Stripe requires an API key",
                error_code="MISSING_CREDENTIALS"
            )
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    "https://api.stripe.com/v1/account",
                    auth=(api_key, ""),
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    account_name = data.get("business_profile", {}).get("name") or data.get("email", "Unknown")
                    return ConnectorTestResult(
                        success=True,
                        message=f"Successfully connected to Stripe: {account_name}",
                        details={"account": account_name}
                    )
                elif response.status_code == 401:
                    return ConnectorTestResult(
                        success=False,
                        message="Invalid API key",
                        error_code="INVALID_KEY"
                    )
                else:
                    return ConnectorTestResult(
                        success=False,
                        message=f"Failed to connect: HTTP {response.status_code}",
                        error_code="CONNECTION_FAILED"
                    )
        except Exception as e:
            return ConnectorTestResult(
                success=False,
                message=f"Connection error: {str(e)}",
                error_code="NETWORK_ERROR"
            )
    
    async def _test_rest_api(self, config: dict) -> ConnectorTestResult:
        """Test generic REST API connection."""
        url = config.get("url")
        method = config.get("method", "GET").upper()
        headers_str = config.get("headers", "{}")
        
        if not url:
            return ConnectorTestResult(
                success=False,
                message="REST API requires a URL",
                error_code="MISSING_URL"
            )
        
        try:
            import json
            headers = json.loads(headers_str) if isinstance(headers_str, str) else headers_str
        except:
            headers = {}
        
        try:
            async with httpx.AsyncClient() as client:
                if method == "GET":
                    response = await client.get(url, headers=headers, timeout=10.0)
                elif method == "POST":
                    response = await client.post(url, headers=headers, timeout=10.0)
                else:
                    return ConnectorTestResult(
                        success=False,
                        message=f"Unsupported HTTP method: {method}",
                        error_code="INVALID_METHOD"
                    )
                
                if 200 <= response.status_code < 300:
                    return ConnectorTestResult(
                        success=True,
                        message=f"Successfully connected to {url}",
                        details={"status_code": response.status_code}
                    )
                else:
                    return ConnectorTestResult(
                        success=False,
                        message=f"API returned HTTP {response.status_code}",
                        error_code="CONNECTION_FAILED"
                    )
        except Exception as e:
            return ConnectorTestResult(
                success=False,
                message=f"Connection error: {str(e)}",
                error_code="NETWORK_ERROR"
            )
    
    async def _test_postgres(self, config: dict) -> ConnectorTestResult:
        """Test PostgreSQL database connection."""
        host = config.get("host")
        port = config.get("port", 5432)
        database = config.get("database")
        username = config.get("username")
        password = config.get("password")
        
        if not all([host, database, username, password]):
            return ConnectorTestResult(
                success=False,
                message="PostgreSQL requires host, database, username, and password",
                error_code="MISSING_CREDENTIALS"
            )
        
        try:
            import asyncpg
            
            conn = await asyncpg.connect(
                host=host,
                port=int(port),
                database=database,
                user=username,
                password=password,
                timeout=10.0
            )
            
            # Test with a simple query
            version = await conn.fetchval("SELECT version()")
            await conn.close()
            
            return ConnectorTestResult(
                success=True,
                message=f"Successfully connected to PostgreSQL database '{database}'",
                details={"database": database, "host": host}
            )
        except ImportError:
            return ConnectorTestResult(
                success=False,
                message="PostgreSQL support not installed. Install asyncpg to use PostgreSQL connectors.",
                error_code="MISSING_DEPENDENCY"
            )
        except Exception as e:
            return ConnectorTestResult(
                success=False,
                message=f"Connection failed: {str(e)}",
                error_code="CONNECTION_FAILED"
            )
