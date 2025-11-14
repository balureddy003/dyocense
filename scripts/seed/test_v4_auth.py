"""
Test script to verify v4 authentication flow.
"""

import asyncio
import httpx


async def test_auth():
    """Test login and protected endpoints."""
    base_url = "http://127.0.0.1:8001"
    
    # Test credentials from seed script
    credentials = {
        "email": "admin@acme.com",
        "password": "password123",
        "tenant_id": "8278e5e6-574b-429f-9f65-2c25fa776ee9"
    }
    
    async with httpx.AsyncClient() as client:
        print("=" * 60)
        print("Testing v4 Authentication Flow")
        print("=" * 60)
        
        # 1. Login
        print("\n1. POST /api/v1/auth/login")
        try:
            response = await client.post(
                f"{base_url}/api/v1/auth/login",
                json=credentials
            )
            response.raise_for_status()
            login_data = response.json()
            token = login_data["access_token"]
            print(f"   ✓ Login successful")
            print(f"   Token: {token[:50]}...")
        except Exception as e:
            print(f"   ✗ Login failed: {e}")
            return
        
        # 2. Get current user
        print("\n2. GET /api/v1/auth/me")
        try:
            response = await client.get(
                f"{base_url}/api/v1/auth/me",
                headers={"Authorization": f"Bearer {token}"}
            )
            response.raise_for_status()
            user_data = response.json()
            print(f"   ✓ User info retrieved")
            print(f"   Email: {user_data['email']}")
            print(f"   Role: {user_data['role']}")
            print(f"   Tenant: {user_data['tenant_id']}")
        except Exception as e:
            print(f"   ✗ Get user failed: {e}")
            return
        
        # 3. List users (tenant-scoped)
        print("\n3. GET /api/v1/users/")
        try:
            response = await client.get(
                f"{base_url}/api/v1/users/",
                headers={"Authorization": f"Bearer {token}"}
            )
            response.raise_for_status()
            users = response.json()
            print(f"   ✓ Users retrieved: {len(users)} users")
            for u in users:
                print(f"   - {u['email']} ({u['role']})")
        except Exception as e:
            print(f"   ✗ List users failed: {e}")
        
        # 4. List workspaces (tenant-scoped)
        print("\n4. GET /api/v1/workspaces/")
        try:
            response = await client.get(
                f"{base_url}/api/v1/workspaces/",
                headers={"Authorization": f"Bearer {token}"}
            )
            response.raise_for_status()
            workspaces = response.json()
            print(f"   ✓ Workspaces retrieved: {len(workspaces)} workspaces")
            for w in workspaces:
                print(f"   - {w['name']}: {w.get('description', 'N/A')}")
        except Exception as e:
            print(f"   ✗ List workspaces failed: {e}")
        
        # 5. Test connector endpoints
        print("\n5. GET /api/v1/connectors/")
        try:
            response = await client.get(
                f"{base_url}/api/v1/connectors/",
                headers={"Authorization": f"Bearer {token}"}
            )
            response.raise_for_status()
            connectors = response.json()
            print(f"   ✓ Connectors retrieved: {len(connectors)} connectors")
        except Exception as e:
            print(f"   ✗ List connectors failed: {e}")
        
        print("\n" + "=" * 60)
        print("All tests completed!")
        print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_auth())
