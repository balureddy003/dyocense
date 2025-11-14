#!/usr/bin/env python3
"""
Phase 0 - Step 1: PostgreSQL Extensions Setup

Sets up all required PostgreSQL extensions for v4.0:
- TimescaleDB (time-series data)
- pgvector (embeddings)
- Apache AGE (graph queries)
- pg_cron (scheduled jobs)
- pgcrypto (encryption)

Usage:
    python scripts/phase0_setup_postgres_extensions.py
"""

import os
import sys
import logging
from pathlib import Path

import psycopg2
from psycopg2 import sql

# Add packages to path
sys.path.insert(0, str(Path(__file__).parent.parent))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)


def get_postgres_connection():
    """Get PostgreSQL connection from environment."""
    return psycopg2.connect(
        host=os.getenv("POSTGRES_HOST", "localhost"),
        port=int(os.getenv("POSTGRES_PORT", "5432")),
        dbname=os.getenv("POSTGRES_DB", "dyocense"),
        user=os.getenv("POSTGRES_USER", "dyocense"),
        password=os.getenv("POSTGRES_PASSWORD", "pass@1234")
    )


def setup_extensions(conn):
    """Install and verify all required PostgreSQL extensions."""
    
    extensions = [
        ("uuid-ossp", "UUID generation"),
        ("pgcrypto", "Cryptographic functions"),
        ("pg_trgm", "Text search"),
        ("vector", "pgvector for embeddings"),
        ("timescaledb", "TimescaleDB for time-series (optional)"),
        ("age", "Apache AGE for graph queries (optional)"),
        ("pg_cron", "Scheduled jobs (optional)")
    ]
    
    cursor = conn.cursor()
    
    for ext_name, description in extensions:
        try:
            logger.info(f"Installing extension: {ext_name} ({description})")
            cursor.execute(sql.SQL("CREATE EXTENSION IF NOT EXISTS {} CASCADE").format(
                sql.Identifier(ext_name)
            ))
            conn.commit()
            logger.info(f"✅ {ext_name} installed successfully")
        except psycopg2.Error as e:
            if "optional" in description.lower():
                logger.warning(f"⚠️  {ext_name} failed to install (optional): {e}")
                conn.rollback()
            else:
                logger.error(f"❌ {ext_name} failed to install (required): {e}")
                conn.rollback()
                raise
    
    cursor.close()


def verify_extensions(conn):
    """Verify installed extensions."""
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT extname, extversion 
        FROM pg_extension 
        WHERE extname IN ('uuid-ossp', 'pgcrypto', 'pg_trgm', 'vector', 'timescaledb', 'age', 'pg_cron')
        ORDER BY extname
    """)
    
    installed = cursor.fetchall()
    
    logger.info("\n" + "="*60)
    logger.info("Installed PostgreSQL Extensions:")
    logger.info("="*60)
    
    for ext_name, version in installed:
        logger.info(f"  ✅ {ext_name:20s} v{version}")
    
    logger.info("="*60 + "\n")
    
    cursor.close()


def create_timescale_hypertables(conn):
    """Create TimescaleDB hypertables for time-series data."""
    cursor = conn.cursor()
    
    # Check if TimescaleDB is available
    cursor.execute("SELECT extname FROM pg_extension WHERE extname = 'timescaledb'")
    if not cursor.fetchone():
        logger.warning("TimescaleDB not installed, skipping hypertable creation")
        cursor.close()
        return
    
    logger.info("Creating TimescaleDB hypertables...")
    
    # Create metrics table if not exists
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS metrics (
            time TIMESTAMPTZ NOT NULL,
            tenant_id TEXT NOT NULL,
            metric_type TEXT NOT NULL,
            metric_value NUMERIC NOT NULL,
            tags JSONB,
            created_at TIMESTAMPTZ DEFAULT NOW()
        )
    """)
    
    try:
        # Convert to hypertable
        cursor.execute("""
            SELECT create_hypertable(
                'metrics', 
                'time', 
                if_not_exists => TRUE,
                chunk_time_interval => INTERVAL '1 day'
            )
        """)
        conn.commit()
        logger.info("✅ Metrics hypertable created")
    except psycopg2.Error as e:
        if "already a hypertable" in str(e):
            logger.info("✅ Metrics hypertable already exists")
            conn.rollback()
        else:
            raise
    
    # Create indices
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_metrics_tenant_time 
        ON metrics (tenant_id, time DESC)
    """)
    
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_metrics_type 
        ON metrics (metric_type, time DESC)
    """)
    
    conn.commit()
    logger.info("✅ Metrics indices created")
    
    cursor.close()


def setup_pgvector_tables(conn):
    """Create pgvector tables for embeddings."""
    cursor = conn.cursor()
    
    # Check if pgvector is available
    cursor.execute("SELECT extname FROM pg_extension WHERE extname = 'vector'")
    if not cursor.fetchone():
        logger.warning("pgvector not installed, skipping vector table creation")
        cursor.close()
        return
    
    logger.info("Creating pgvector embeddings table...")
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS embeddings (
            embedding_id TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
            tenant_id TEXT NOT NULL,
            content TEXT NOT NULL,
            embedding vector(1536),  -- OpenAI ada-002 dimension
            metadata JSONB,
            created_at TIMESTAMPTZ DEFAULT NOW()
        )
    """)
    
    # Create HNSW index for fast similarity search
    try:
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_embeddings_hnsw 
            ON embeddings USING hnsw (embedding vector_cosine_ops)
        """)
        logger.info("✅ HNSW index created (best performance)")
    except psycopg2.Error:
        # Fall back to IVFFlat if HNSW not available
        logger.warning("HNSW not available, using IVFFlat index")
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_embeddings_ivfflat 
            ON embeddings USING ivfflat (embedding vector_cosine_ops)
            WITH (lists = 100)
        """)
        logger.info("✅ IVFFlat index created")
    
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_embeddings_tenant 
        ON embeddings (tenant_id)
    """)
    
    conn.commit()
    logger.info("✅ Embeddings table and indices created")
    
    cursor.close()


def setup_pg_cron_jobs(conn):
    """Set up pg_cron scheduled jobs."""
    cursor = conn.cursor()
    
    # Check if pg_cron is available
    cursor.execute("SELECT extname FROM pg_extension WHERE extname = 'pg_cron'")
    if not cursor.fetchone():
        logger.warning("pg_cron not installed, skipping job setup")
        cursor.close()
        return
    
    logger.info("Setting up pg_cron jobs...")
    
    # Example: Clean up old sessions daily
    try:
        cursor.execute("""
            SELECT cron.schedule(
                'cleanup-old-sessions',
                '0 2 * * *',  -- Daily at 2 AM
                $$DELETE FROM trust.sessions WHERE expires_at < NOW()$$
            )
        """)
        logger.info("✅ Session cleanup job scheduled")
    except psycopg2.Error as e:
        if "already exists" in str(e):
            logger.info("✅ Session cleanup job already exists")
            conn.rollback()
        else:
            logger.warning(f"⚠️  Failed to schedule session cleanup: {e}")
            conn.rollback()
    
    cursor.close()


def main():
    """Main execution."""
    logger.info("="*60)
    logger.info("Phase 0 - PostgreSQL Extensions Setup")
    logger.info("="*60)
    
    try:
        conn = get_postgres_connection()
        logger.info("✅ Connected to PostgreSQL")
        
        # Step 1: Install extensions
        setup_extensions(conn)
        
        # Step 2: Verify installations
        verify_extensions(conn)
        
        # Step 3: Create TimescaleDB hypertables
        create_timescale_hypertables(conn)
        
        # Step 4: Create pgvector tables
        setup_pgvector_tables(conn)
        
        # Step 5: Set up pg_cron jobs
        setup_pg_cron_jobs(conn)
        
        conn.close()
        
        logger.info("\n" + "="*60)
        logger.info("✅ Phase 0 - PostgreSQL Extensions Setup Complete!")
        logger.info("="*60)
        logger.info("\nNext steps:")
        logger.info("  1. Run: python scripts/phase0_migrate_influxdb.py")
        logger.info("  2. Run: python scripts/phase0_migrate_pinecone.py")
        logger.info("  3. Run: python scripts/phase0_validate_migration.py")
        
    except Exception as e:
        logger.error(f"❌ Setup failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
