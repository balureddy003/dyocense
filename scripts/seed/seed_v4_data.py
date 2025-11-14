"""
Seed script for v4 tables with test tenant, users, and workspaces.

Run with: python -m scripts.seed.seed_v4_data
"""

import asyncio
import uuid
from datetime import datetime

from backend.config import settings
from backend.dependencies import AsyncSessionLocal
from backend.models.tenant import Tenant
from backend.models.user import User
from backend.models.workspace import Workspace
from backend.utils.auth import hash_password


async def seed_v4_data():
    """Create test tenant, users, and workspaces for development."""
    async with AsyncSessionLocal() as db:
        try:
            # Create test tenant
            tenant_id = uuid.uuid4()
            tenant = Tenant(
                id=tenant_id,
                name="Acme Corp",
                subscription_status="active",
            )
            db.add(tenant)
            await db.flush()
            
            print(f"✓ Created tenant: {tenant.name} (ID: {tenant_id})")
            
            # Create admin user
            admin = User(
                id=uuid.uuid4(),
                tenant_id=tenant_id,
                email="admin@acme.com",
                hashed_password=hash_password("password123"),
                role="admin",
                is_active=True,
            )
            db.add(admin)
            
            # Create regular user
            user = User(
                id=uuid.uuid4(),
                tenant_id=tenant_id,
                email="user@acme.com",
                hashed_password=hash_password("password123"),
                role="user",
                is_active=True,
            )
            db.add(user)
            
            await db.flush()
            print(f"✓ Created admin: {admin.email}")
            print(f"✓ Created user: {user.email}")
            
            # Create workspaces
            workspace1 = Workspace(
                id=uuid.uuid4(),
                tenant_id=tenant_id,
                name="Sales Analytics",
                description="Revenue forecasting and pipeline optimization",
            )
            db.add(workspace1)
            
            workspace2 = Workspace(
                id=uuid.uuid4(),
                tenant_id=tenant_id,
                name="Operations",
                description="Inventory and staffing optimization",
            )
            db.add(workspace2)
            
            await db.flush()
            print(f"✓ Created workspace: {workspace1.name}")
            print(f"✓ Created workspace: {workspace2.name}")
            
            await db.commit()
            
            print("\n" + "="*60)
            print("TEST CREDENTIALS")
            print("="*60)
            print(f"Tenant ID: {tenant_id}")
            print(f"Admin: admin@acme.com / password123")
            print(f"User: user@acme.com / password123")
            print("="*60)
            
            return {
                "tenant_id": str(tenant_id),
                "admin_email": admin.email,
                "user_email": user.email,
            }
            
        except Exception as e:
            await db.rollback()
            print(f"✗ Error seeding data: {e}")
            raise


if __name__ == "__main__":
    asyncio.run(seed_v4_data())
