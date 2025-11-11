#!/usr/bin/env python3
"""
Create test tenant for CycloneRake to verify E2E flow
"""
import os
import sys
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
import uuid

# PostgreSQL connection
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")
POSTGRES_DB = os.getenv("POSTGRES_DB", "dyocense")
POSTGRES_USER = os.getenv("POSTGRES_USER", "dyocense")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "pass@1234")

# CycloneRake tenant data
TENANT_ID = "cyclonerake-demo001"
TENANT_NAME = "CycloneRake"
OWNER_EMAIL = "owner@cyclonerake.com"
API_TOKEN = f"key-{uuid.uuid4().hex[:16]}"

print(f"Creating test tenant for CycloneRake...")
print(f"Tenant ID: {TENANT_ID}")
print(f"Owner: {OWNER_EMAIL}\n")

conn = None
try:
    conn = psycopg2.connect(
        host=POSTGRES_HOST,
        port=POSTGRES_PORT,
        database=POSTGRES_DB,
        user=POSTGRES_USER,
        password=POSTGRES_PASSWORD,
        cursor_factory=RealDictCursor
    )
    conn.autocommit = True
    
    with conn.cursor() as cur:
        # 1. Check if tenant already exists
        cur.execute("""
            SELECT tenant_id, name, owner_email 
            FROM tenants.tenants 
            WHERE tenant_id = %s
        """, (TENANT_ID,))
        
        existing = cur.fetchone()
        if existing:
            print(f"✅ Tenant already exists: {existing['name']}")
            print(f"   Owner: {existing['owner_email']}")
            print(f"   Tenant ID: {existing['tenant_id']}")
            sys.exit(0)
        
        print("Creating new tenant...")
        
        # 2. Create tenant
        cur.execute("""
            INSERT INTO tenants.tenants (
                tenant_id,
                name,
                owner_email,
                status,
                api_token,
                created_at,
                updated_at,
                metadata
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING tenant_id
        """, (
            TENANT_ID,
            TENANT_NAME,
            OWNER_EMAIL,
            'active',
            API_TOKEN,
            datetime.utcnow(),
            datetime.utcnow(),
            {
                'industry': 'retail',
                'signup_method': 'test',
                'created_for': 'E2E testing with ERPNext'
            }
        ))
        
        result = cur.fetchone()
        print(f"✅ Created tenant: {result['tenant_id']}")
        
        # 3. Create owner user
        user_id = str(uuid.uuid4())
        cur.execute("""
            INSERT INTO tenants.users (
                user_id,
                tenant_id,
                email,
                full_name,
                password_hash,
                roles,
                created_at,
                updated_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING user_id
        """, (
            user_id,
            TENANT_ID,
            OWNER_EMAIL,
            "John Doe (CycloneRake Owner)",
            "",  # No password for test user
            ['owner'],
            datetime.utcnow(),
            datetime.utcnow()
        ))
        
        print(f"✅ Created owner user: {user_id}")
        
        # 4. Create default workspace/project
        project_id = str(uuid.uuid4())
        cur.execute("""
            INSERT INTO tenants.projects (
                project_id,
                tenant_id,
                name,
                description,
                status,
                created_at,
                updated_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING project_id
        """, (
            project_id,
            TENANT_ID,
            "Default Workspace",
            "Main workspace for CycloneRake operations",
            'active',
            datetime.utcnow(),
            datetime.utcnow()
        ))
        
        print(f"✅ Created workspace: {project_id}")
        
        print(f"\n{'='*60}")
        print(f"✅ CycloneRake tenant setup complete!")
        print(f"{'='*60}")
        print(f"\nTenant Details:")
        print(f"  Tenant ID:  {TENANT_ID}")
        print(f"  Name:       {TENANT_NAME}")
        print(f"  Owner:      {OWNER_EMAIL}")
        print(f"  API Token:  {API_TOKEN}")
        print(f"  User ID:    {user_id}")
        print(f"  Workspace:  {project_id}")
        
        print(f"\nNext Steps:")
        print(f"1. Setup ERPNext connector:")
        print(f"   curl -X POST http://localhost:8001/api/connectors/erpnext/setup \\")
        print(f"     -H 'Content-Type: application/json' \\")
        print(f"     -d '{{")
        print(f"       \"tenant_id\": \"{TENANT_ID}\",")
        print(f"       \"user_id\": \"{user_id}\",")
        print(f"       \"name\": \"CycloneRake ERP\",")
        print(f"       \"api_url\": \"https://erp.cyclonerake.com\",")
        print(f"       \"api_key\": \"YOUR_ERPNEXT_KEY\",")
        print(f"       \"api_secret\": \"YOUR_ERPNEXT_SECRET\"")
        print(f"     }}'")
        
        print(f"\n2. Trigger sync to fetch data")
        print(f"3. Use AI coach with real CycloneRake data")
        
except psycopg2.Error as e:
    print(f"❌ Database error: {e}")
    sys.exit(1)
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
finally:
    if conn:
        conn.close()
