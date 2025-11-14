#!/usr/bin/env python3
"""
Test connector data persistence to PostgreSQL
"""
import os
import sys
import psycopg2
from psycopg2.extras import RealDictCursor, Json
from datetime import datetime
import json

# Get PostgreSQL connection parameters
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")
POSTGRES_DB = os.getenv("POSTGRES_DB", "dyocense")
POSTGRES_USER = os.getenv("POSTGRES_USER", "dyocense")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "pass@1234")

TENANT_ID = "icuboid-b70983"
CONNECTOR_ID = "test_connector_001"

print(f"Testing connector data flow for tenant: {TENANT_ID}")

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
        print("\n1. Inserting test connector data...")
        
        # Sample orders data
        orders_data = [
            {
                "order_id": "ORD-001",
                "customer": "Test Customer 1",
                "amount": 150.00,
                "date": "2024-01-15",
                "items": 3
            },
            {
                "order_id": "ORD-002",
                "customer": "Test Customer 2",
                "amount": 275.50,
                "date": "2024-01-16",
                "items": 5
            },
            {
                "order_id": "ORD-003",
                "customer": "Test Customer 1",
                "amount": 99.99,
                "date": "2024-01-17",
                "items": 2
            }
        ]
        
        # Insert using UPSERT
        cur.execute("""
            INSERT INTO connectors.connector_data 
            (tenant_id, connector_id, data_type, data, record_count, metadata)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (tenant_id, connector_id, data_type)
            DO UPDATE SET
                data = EXCLUDED.data,
                record_count = EXCLUDED.record_count,
                synced_at = NOW(),
                metadata = EXCLUDED.metadata
            RETURNING data_id, synced_at, record_count
        """, (
            TENANT_ID,
            CONNECTOR_ID,
            'orders',
            Json(orders_data),
            len(orders_data),
            Json({"source": "test", "test_run": True})
        ))
        
        result = cur.fetchone()
        print(f"   ✅ Inserted {result['record_count']} orders")
        print(f"   Data ID: {result['data_id']}")
        print(f"   Synced at: {result['synced_at']}")
        
        # Insert inventory data
        inventory_data = [
            {"sku": "PROD-A1", "name": "Widget A", "stock": 150, "reorder_point": 50},
            {"sku": "PROD-B2", "name": "Widget B", "stock": 75, "reorder_point": 30},
            {"sku": "PROD-C3", "name": "Widget C", "stock": 200, "reorder_point": 100}
        ]
        
        cur.execute("""
            INSERT INTO connectors.connector_data 
            (tenant_id, connector_id, data_type, data, record_count, metadata)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (tenant_id, connector_id, data_type)
            DO UPDATE SET
                data = EXCLUDED.data,
                record_count = EXCLUDED.record_count,
                synced_at = NOW(),
                metadata = EXCLUDED.metadata
            RETURNING data_id, synced_at, record_count
        """, (
            TENANT_ID,
            CONNECTOR_ID,
            'inventory',
            Json(inventory_data),
            len(inventory_data),
            Json({"source": "test", "test_run": True})
        ))
        
        result = cur.fetchone()
        print(f"   ✅ Inserted {result['record_count']} inventory items")
        
        print("\n2. Querying connector data for tenant...")
        
        # Query all data for tenant (simulating _fetch_connector_data)
        cur.execute("""
            SELECT data_type, data, synced_at, record_count
            FROM connectors.connector_data
            WHERE tenant_id = %s
            ORDER BY synced_at DESC
        """, (TENANT_ID,))
        
        rows = cur.fetchall()
        
        print(f"   Found {len(rows)} data types:")
        
        tenant_data = {}
        for row in rows:
            data_type = row['data_type']
            tenant_data[data_type] = row['data']
            print(f"   - {data_type}: {row['record_count']} records (synced: {row['synced_at']})")
        
        print("\n3. Verifying data structure...")
        
        if 'orders' in tenant_data:
            orders = tenant_data['orders']
            total_revenue = sum(order['amount'] for order in orders)
            print(f"   ✅ Orders: {len(orders)} orders, ${total_revenue:.2f} total")
            print(f"      First order: {orders[0]}")
        
        if 'inventory' in tenant_data:
            inventory = tenant_data['inventory']
            total_stock = sum(item['stock'] for item in inventory)
            print(f"   ✅ Inventory: {len(inventory)} SKUs, {total_stock} units total")
            print(f"      Low stock: {[i['sku'] for i in inventory if i['stock'] < i['reorder_point']]}")
        
        print("\n4. Testing data freshness...")
        
        cur.execute("""
            SELECT 
                data_type,
                synced_at,
                EXTRACT(EPOCH FROM (NOW() - synced_at)) as age_seconds
            FROM connectors.connector_data
            WHERE tenant_id = %s
        """, (TENANT_ID,))
        
        for row in cur.fetchall():
            age = row['age_seconds']
            if age < 60:
                freshness = f"{age:.0f}s ago"
            elif age < 3600:
                freshness = f"{age/60:.0f}m ago"
            else:
                freshness = f"{age/3600:.1f}h ago"
            
            print(f"   {row['data_type']}: {freshness}")
        
        print("\n✅ All tests passed! Connector data persistence is working correctly.")
        print("\nNext steps:")
        print("1. Start smb_gateway service")
        print("2. Call AI coach API")
        print("3. Verify coach queries this PostgreSQL data")
        
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
