"""
Connector Testing Service
Tests connector configurations before they are saved.
"""
import logging
from typing import Any, Dict
import httpx
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class ConnectorTestResult(BaseModel):
    """Result of a connector test"""
    success: bool
    message: str
    details: Dict[str, Any] = {}
    error_code: str | None = None


class ConnectorTester:
    """Test connector configurations to ensure they work."""
    
    def __init__(self):
        self.timeout = 15.0  # seconds
    
    async def test(self, connector_type: str, config: Dict[str, Any]) -> ConnectorTestResult:
        """Test a connector configuration."""
        # Route to specific test method
        if connector_type == "salesforce":
            return await self._test_salesforce(config)
        elif connector_type == "csv_upload":
            return ConnectorTestResult(
                success=True,
                message="CSV upload ready"
            )
        else:
            return ConnectorTestResult(
                success=True,
                message=f"Connector type '{connector_type}' configured (testing not yet implemented)"
            )
    
    async def _test_salesforce(self, config: Dict[str, Any]) -> ConnectorTestResult:
        """Test Salesforce connection using OAuth password flow."""
        instance_url = config.get("instance_url", "").rstrip("/")
        username = config.get("username")
        password = config.get("password")
        security_token = config.get("security_token", "")
        client_id = config.get("client_id")
        client_secret = config.get("client_secret")
        
        # Validate required fields
        if not all([instance_url, username, password, client_id, client_secret]):
            missing = []
            if not instance_url: missing.append("instance_url")
            if not username: missing.append("username")
            if not password: missing.append("password")
            if not client_id: missing.append("client_id")
            if not client_secret: missing.append("client_secret")
            
            return ConnectorTestResult(
                success=False,
                message=f"Missing required fields: {', '.join(missing)}",
                error_code="MISSING_FIELDS"
            )
        
        # Validate instance URL format
        if not instance_url.startswith("https://"):
            return ConnectorTestResult(
                success=False,
                message="Instance URL must start with https://",
                error_code="INVALID_URL"
            )
        
        try:
            # Attempt OAuth password flow authentication
            auth_url = f"{instance_url}/services/oauth2/token"
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    auth_url,
                    data={
                        'grant_type': 'password',
                        'client_id': client_id,
                        'client_secret': client_secret,
                        'username': username,
                        'password': f"{password}{security_token}",
                    },
                    timeout=self.timeout
                )
                
                if response.status_code == 200:
                    auth_data = response.json()
                    access_token = auth_data.get('access_token')
                    
                    # Test the access token by fetching organization info
                    if access_token:
                        limits_url = f"{instance_url}/services/data/v58.0/limits"
                        limits_response = await client.get(
                            limits_url,
                            headers={'Authorization': f'Bearer {access_token}'},
                            timeout=self.timeout
                        )
                        
                        if limits_response.status_code == 200:
                            limits_data = limits_response.json()
                            api_usage = limits_data.get('DailyApiRequests', {})
                            
                            return ConnectorTestResult(
                                success=True,
                                message="Successfully connected to Salesforce",
                                details={
                                    "instance_url": instance_url,
                                    "api_requests_used": api_usage.get('Used', 0),
                                    "api_requests_limit": api_usage.get('Max', 0)
                                }
                            )
                
                # Handle authentication errors
                if response.status_code == 400:
                    error_data = response.json()
                    error_desc = error_data.get('error_description', 'Invalid credentials')
                    
                    if 'invalid_grant' in error_data.get('error', ''):
                        return ConnectorTestResult(
                            success=False,
                            message=f"Authentication failed: {error_desc}. Please check your username, password, and security token.",
                            error_code="INVALID_CREDENTIALS"
                        )
                    
                    return ConnectorTestResult(
                        success=False,
                        message=f"Authentication failed: {error_desc}",
                        error_code="AUTH_FAILED"
                    )
                
                elif response.status_code == 401:
                    return ConnectorTestResult(
                        success=False,
                        message="Invalid client credentials. Please check your Consumer Key and Secret.",
                        error_code="INVALID_CLIENT"
                    )
                
                else:
                    return ConnectorTestResult(
                        success=False,
                        message=f"Connection failed: HTTP {response.status_code}",
                        error_code="CONNECTION_FAILED"
                    )
        
        except httpx.TimeoutException:
            return ConnectorTestResult(
                success=False,
                message="Connection timeout. Please check your instance URL and network connection.",
                error_code="TIMEOUT"
            )
        except httpx.ConnectError:
            return ConnectorTestResult(
                success=False,
                message="Cannot connect to Salesforce. Please verify your instance URL.",
                error_code="NETWORK_ERROR"
            )
        except Exception as e:
            logger.error(f"Salesforce test error: {e}")
            return ConnectorTestResult(
                success=False,
                message=f"Test failed: {str(e)}",
                error_code="TEST_ERROR"
            )
