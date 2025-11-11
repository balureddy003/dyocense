#!/usr/bin/env python3
"""
Database Migration Runner

Runs SQL migration files in the migrations directory.
Usage: python run_migration.py <migration_file>
"""

import os
import sys
import psycopg2
from psycopg2.extras import RealDictCursor


def get_db_connection():
    """Get PostgreSQL connection from environment"""
    postgres_url = os.getenv("POSTGRES_URL")
    if not postgres_url:
        print("❌ Error: POSTGRES_URL environment variable not set")
        sys.exit(1)
    
    try:
        conn = psycopg2.connect(postgres_url, cursor_factory=RealDictCursor)
        return conn
    except Exception as e:
        print(f"❌ Error connecting to database: {e}")
        sys.exit(1)


def run_migration(migration_file: str):
    """Run a SQL migration file"""
    if not os.path.exists(migration_file):
        print(f"❌ Error: Migration file not found: {migration_file}")
        sys.exit(1)
    
    print(f"📂 Reading migration file: {migration_file}")
    
    with open(migration_file, 'r') as f:
        sql = f.read()
    
    print(f"🔌 Connecting to database...")
    conn = get_db_connection()
    
    try:
        with conn.cursor() as cur:
            print(f"⚡ Executing migration...")
            cur.execute(sql)
            conn.commit()
            print(f"✅ Migration completed successfully!")
            
            # Print any notices
            if conn.notices:
                print("\n📋 Migration notices:")
                for notice in conn.notices:
                    print(f"   {notice.strip()}")
    
    except Exception as e:
        conn.rollback()
        print(f"❌ Migration failed: {e}")
        sys.exit(1)
    
    finally:
        conn.close()


def main():
    if len(sys.argv) < 2:
        print("Usage: python run_migration.py <migration_file>")
        print("\nExample:")
        print("  python run_migration.py infra/postgres/migrations/001_full_schema.sql")
        sys.exit(1)
    
    migration_file = sys.argv[1]
    
    print("=" * 60)
    print("Database Migration Runner")
    print("=" * 60)
    
    run_migration(migration_file)
    
    print("=" * 60)


if __name__ == '__main__':
    main()
