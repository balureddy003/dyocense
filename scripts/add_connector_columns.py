#!/usr/bin/env python3
"""
Manually add missing columns to connectors.connectors table
"""
import os
import psycopg2
from urllib.parse import urlparse

def main():
    postgres_url = os.getenv("POSTGRES_URL")
    if not postgres_url:
        print("❌ POSTGRES_URL not set")
        return
    
    print(f"🔍 Connecting to database...")
    
    # Parse the URL manually to handle password with @ symbol
    # Format: postgresql://user:pass@host:port/database
    if postgres_url.startswith("postgresql://"):
        postgres_url = postgres_url.replace("postgresql://", "")
    
    # Split at the last @ to get host part
    parts = postgres_url.rsplit("@", 1)
    if len(parts) != 2:
        print("❌ Invalid POSTGRES_URL format")
        return
    
    user_pass = parts[0]
    host_db = parts[1]
    
    # Split user:pass
    if ":" in user_pass:
        user, password = user_pass.split(":", 1)
    else:
        print("❌ No password in POSTGRES_URL")
        return
    
    # Split host:port/database
    if "/" in host_db:
        host_port, database = host_db.split("/", 1)
    else:
        print("❌ No database in POSTGRES_URL")
        return
    
    if ":" in host_port:
        host, port = host_port.split(":", 1)
    else:
        host = host_port
        port = "5432"
    
    print(f"Host: {host}")
    print(f"Port: {port}")
    print(f"User: {user}")
    print(f"Database: {database}")
    
    try:
        conn = psycopg2.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            database=database
        )
        
        print("✅ Connected to database")
        
        with conn.cursor() as cur:
            print("🔍 Checking for missing columns...")
            
            # Check if sync_frequency exists
            cur.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_schema = 'connectors' 
                AND table_name = 'connectors' 
                AND column_name = 'sync_frequency'
            """)
            
            if cur.fetchone():
                print("✅ sync_frequency column already exists")
            else:
                print("⚠️ sync_frequency column missing - adding it...")
                
                cur.execute("""
                    ALTER TABLE connectors.connectors 
                    ADD COLUMN IF NOT EXISTS connector_name TEXT NOT NULL DEFAULT '',
                    ADD COLUMN IF NOT EXISTS display_name TEXT NOT NULL DEFAULT '',
                    ADD COLUMN IF NOT EXISTS category TEXT,
                    ADD COLUMN IF NOT EXISTS icon TEXT,
                    ADD COLUMN IF NOT EXISTS data_types TEXT[] DEFAULT ARRAY[]::TEXT[],
                    ADD COLUMN IF NOT EXISTS sync_frequency TEXT DEFAULT 'manual',
                    ADD COLUMN IF NOT EXISTS created_by TEXT,
                    ADD COLUMN IF NOT EXISTS sync_status TEXT,
                    ADD COLUMN IF NOT EXISTS sync_error TEXT,
                    ADD COLUMN IF NOT EXISTS metadata JSONB DEFAULT '{}'
                """)
                print("✅ Columns added")
                
                # Update existing rows
                cur.execute("""
                    UPDATE connectors.connectors 
                    SET connector_name = COALESCE(connector_name, connector_type, ''),
                        display_name = COALESCE(display_name, connector_type, ''),
                        sync_frequency = COALESCE(sync_frequency, 'manual')
                    WHERE connector_name = '' OR display_name = ''
                """)
                print("✅ Existing rows updated")
                
                conn.commit()
                print("✅ Migration completed successfully!")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
