#!/usr/bin/env python3
"""
Migration script to add connector_data table to PostgreSQL
"""
import os
import sys
import psycopg2
from psycopg2 import sql

# Get PostgreSQL connection parameters
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")
POSTGRES_DB = os.getenv("POSTGRES_DB", "dyocense")
POSTGRES_USER = os.getenv("POSTGRES_USER", "dyocense")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "pass@1234")

print(f"Connecting to PostgreSQL at {POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}...")

conn = None
try:
    conn = psycopg2.connect(
        host=POSTGRES_HOST,
        port=POSTGRES_PORT,
        database=POSTGRES_DB,
        user=POSTGRES_USER,
        password=POSTGRES_PASSWORD
    )
    conn.autocommit = True
    
    with conn.cursor() as cur:
        # Check if table already exists
        cur.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'connectors' 
                AND table_name = 'connector_data'
            );
        """)
        
        exists = cur.fetchone()[0]
        
        if exists:
            print("✅ connector_data table already exists")
            sys.exit(0)
        
        print("Creating connector_data table...")
        
        # Create the table
        cur.execute("""
            CREATE TABLE connectors.connector_data (
              data_id TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
              tenant_id TEXT NOT NULL REFERENCES tenants.tenants(tenant_id) ON DELETE CASCADE,
              connector_id TEXT NOT NULL REFERENCES connectors.connectors(connector_id) ON DELETE CASCADE,
              data_type TEXT NOT NULL, -- 'orders', 'inventory', 'customers', 'products', etc.
              data JSONB NOT NULL, -- Array of records from external system
              synced_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
              record_count INTEGER DEFAULT 0,
              metadata JSONB DEFAULT '{}',
              
              CONSTRAINT unique_tenant_connector_datatype UNIQUE(tenant_id, connector_id, data_type)
            );
        """)
        
        print("Creating indexes...")
        
        cur.execute("""
            CREATE INDEX idx_connector_data_tenant ON connectors.connector_data(tenant_id, connector_id);
        """)
        
        cur.execute("""
            CREATE INDEX idx_connector_data_type ON connectors.connector_data(data_type);
        """)
        
        cur.execute("""
            CREATE INDEX idx_connector_data_synced ON connectors.connector_data(synced_at DESC);
        """)
        
        print("✅ Migration completed successfully!")
        print("\nTable structure:")
        
        # Show table structure
        cur.execute("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_schema = 'connectors' AND table_name = 'connector_data'
            ORDER BY ordinal_position;
        """)
        
        for row in cur.fetchall():
            print(f"  - {row[0]}: {row[1]} ({'NULL' if row[2] == 'YES' else 'NOT NULL'})")
        
except psycopg2.Error as e:
    print(f"❌ Database error: {e}")
    sys.exit(1)
except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)
finally:
    if conn:
        conn.close()
