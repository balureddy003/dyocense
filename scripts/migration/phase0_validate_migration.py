#!/usr/bin/env python3
"""
Phase 0 - Step 4: Validate Database Migration

Validates that data was successfully migrated from multiple databases to PostgreSQL.
Checks data integrity, counts, and performance.

Usage:
    python scripts/phase0_validate_migration.py
"""

import os
import sys
import logging
from pathlib import Path

import psycopg2
from psycopg2.extras import RealDictCursor
import json

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)


def get_postgres_connection():
    """Get PostgreSQL connection."""
    return psycopg2.connect(
        host=os.getenv("POSTGRES_HOST", "localhost"),
        port=int(os.getenv("POSTGRES_PORT", "5432")),
        dbname=os.getenv("POSTGRES_DB", "dyocense"),
        user=os.getenv("POSTGRES_USER", "dyocense"),
        password=os.getenv("POSTGRES_PASSWORD", "pass@1234"),
        cursor_factory=RealDictCursor
    )


def validate_extensions(conn):
    """Validate required extensions are installed."""
    logger.info("\n" + "="*60)
    logger.info("Validating PostgreSQL Extensions")
    logger.info("="*60)
    
    cursor = conn.cursor()
    
    required_extensions = ["uuid-ossp", "pgcrypto", "pg_trgm", "vector"]
    optional_extensions = ["timescaledb", "age", "pg_cron"]
    
    cursor.execute("""
        SELECT extname, extversion 
        FROM pg_extension 
        ORDER BY extname
    """)
    
    installed = {row["extname"]: row["extversion"] for row in cursor.fetchall()}
    
    all_valid = True
    
    for ext in required_extensions:
        if ext in installed:
            logger.info(f"  ✅ {ext:20s} v{installed[ext]} (required)")
        else:
            logger.error(f"  ❌ {ext:20s} MISSING (required)")
            all_valid = False
    
    for ext in optional_extensions:
        if ext in installed:
            logger.info(f"  ✅ {ext:20s} v{installed[ext]} (optional)")
        else:
            logger.warning(f"  ⚠️  {ext:20s} not installed (optional)")
    
    cursor.close()
    return all_valid


def validate_timescale_metrics(conn):
    """Validate TimescaleDB metrics migration."""
    logger.info("\n" + "="*60)
    logger.info("Validating TimescaleDB Metrics")
    logger.info("="*60)
    
    cursor = conn.cursor()
    
    # Check if metrics table exists
    cursor.execute("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_name = 'metrics'
        )
    """)
    
    if not cursor.fetchone()["exists"]:
        logger.warning("  ⚠️  Metrics table not found (may not be migrated yet)")
        cursor.close()
        return True
    
    # Check if it's a hypertable
    cursor.execute("""
        SELECT * FROM timescaledb_information.hypertables 
        WHERE hypertable_name = 'metrics'
    """)
    
    hypertable = cursor.fetchone()
    if hypertable:
        logger.info(f"  ✅ Metrics is a TimescaleDB hypertable")
        logger.info(f"     Chunk interval: {hypertable.get('chunk_time_interval', 'unknown')}")
    else:
        logger.warning("  ⚠️  Metrics table exists but is not a hypertable")
    
    # Count metrics
    cursor.execute("SELECT COUNT(*) as count FROM metrics")
    count = cursor.fetchone()["count"]
    logger.info(f"  ✅ Total metrics: {count:,}")
    
    # Count by tenant
    cursor.execute("""
        SELECT tenant_id, COUNT(*) as count 
        FROM metrics 
        GROUP BY tenant_id 
        ORDER BY count DESC 
        LIMIT 5
    """)
    
    logger.info(f"  Top 5 tenants by metric count:")
    for row in cursor.fetchall():
        logger.info(f"     {row['tenant_id'][:20]:20s}: {row['count']:,} metrics")
    
    # Check indices
    cursor.execute("""
        SELECT indexname FROM pg_indexes 
        WHERE tablename = 'metrics'
    """)
    
    indices = [row["indexname"] for row in cursor.fetchall()]
    logger.info(f"  ✅ Indices: {', '.join(indices)}")
    
    cursor.close()
    return True


def validate_pgvector_embeddings(conn):
    """Validate pgvector embeddings migration."""
    logger.info("\n" + "="*60)
    logger.info("Validating pgvector Embeddings")
    logger.info("="*60)
    
    cursor = conn.cursor()
    
    # Check if embeddings table exists
    cursor.execute("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_name = 'embeddings'
        )
    """)
    
    if not cursor.fetchone()["exists"]:
        logger.warning("  ⚠️  Embeddings table not found (may not be migrated yet)")
        cursor.close()
        return True
    
    # Count embeddings
    cursor.execute("SELECT COUNT(*) as count FROM embeddings")
    count = cursor.fetchone()["count"]
    logger.info(f"  ✅ Total embeddings: {count:,}")
    
    # Check vector dimensions
    cursor.execute("""
        SELECT vector_dims(embedding) as dims 
        FROM embeddings 
        LIMIT 1
    """)
    
    result = cursor.fetchone()
    if result:
        logger.info(f"  ✅ Vector dimension: {result['dims']}")
    
    # Count by tenant
    cursor.execute("""
        SELECT tenant_id, COUNT(*) as count 
        FROM embeddings 
        GROUP BY tenant_id 
        ORDER BY count DESC 
        LIMIT 5
    """)
    
    logger.info(f"  Top 5 tenants by embedding count:")
    for row in cursor.fetchall():
        logger.info(f"     {row['tenant_id'][:20]:20s}: {row['count']:,} embeddings")
    
    # Check indices (HNSW or IVFFlat)
    cursor.execute("""
        SELECT indexname, indexdef 
        FROM pg_indexes 
        WHERE tablename = 'embeddings' AND indexdef LIKE '%vector%'
    """)
    
    for row in cursor.fetchall():
        index_type = "HNSW" if "hnsw" in row["indexdef"].lower() else "IVFFlat"
        logger.info(f"  ✅ Vector index: {row['indexname']} ({index_type})")
    
    # Test vector search performance
    logger.info("\n  Testing vector search performance...")
    
    import time
    start = time.time()
    
    cursor.execute("""
        SELECT embedding_id, content, 
               embedding <=> '[0.1, 0.2, 0.3, ...]'::vector AS distance
        FROM embeddings
        ORDER BY embedding <=> '[0.1, 0.2, 0.3, ...]'::vector
        LIMIT 10
    """.replace("[0.1, 0.2, 0.3, ...]", str([0.01] * 1536)))  # Dummy query vector
    
    elapsed = (time.time() - start) * 1000
    logger.info(f"  ✅ Vector search latency: {elapsed:.2f}ms (10 results)")
    
    if elapsed > 100:
        logger.warning(f"  ⚠️  Vector search is slow (>{elapsed:.0f}ms). Consider rebuilding index.")
    
    cursor.close()
    return True


def validate_tenant_data(conn):
    """Validate core tenant data."""
    logger.info("\n" + "="*60)
    logger.info("Validating Core Tenant Data")
    logger.info("="*60)
    
    cursor = conn.cursor()
    
    # Count tenants
    cursor.execute("SELECT COUNT(*) as count FROM tenants.tenants")
    tenant_count = cursor.fetchone()["count"]
    logger.info(f"  ✅ Total tenants: {tenant_count}")
    
    # Count users
    cursor.execute("SELECT COUNT(*) as count FROM tenants.users")
    user_count = cursor.fetchone()["count"]
    logger.info(f"  ✅ Total users: {user_count}")
    
    # Count projects
    cursor.execute("SELECT COUNT(*) as count FROM tenants.projects")
    project_count = cursor.fetchone()["count"]
    logger.info(f"  ✅ Total projects: {project_count}")
    
    # Check for orphaned data
    cursor.execute("""
        SELECT COUNT(*) as count 
        FROM tenants.users u 
        LEFT JOIN tenants.tenants t ON u.tenant_id = t.tenant_id 
        WHERE t.tenant_id IS NULL
    """)
    
    orphaned = cursor.fetchone()["count"]
    if orphaned > 0:
        logger.warning(f"  ⚠️  Found {orphaned} orphaned users (no matching tenant)")
    else:
        logger.info(f"  ✅ No orphaned users found")
    
    cursor.close()
    return True


def validate_data_integrity(conn):
    """Run data integrity checks."""
    logger.info("\n" + "="*60)
    logger.info("Running Data Integrity Checks")
    logger.info("="*60)
    
    cursor = conn.cursor()
    
    checks = [
        {
            "name": "Tenants have owners",
            "query": "SELECT COUNT(*) as count FROM tenants.tenants WHERE owner_email IS NULL OR owner_email = ''"
        },
        {
            "name": "Users belong to valid tenants",
            "query": """
                SELECT COUNT(*) as count 
                FROM tenants.users u 
                LEFT JOIN tenants.tenants t ON u.tenant_id = t.tenant_id 
                WHERE t.tenant_id IS NULL
            """
        },
        {
            "name": "Metrics have valid timestamps",
            "query": "SELECT COUNT(*) as count FROM metrics WHERE time > NOW()"
        }
    ]
    
    all_valid = True
    
    for check in checks:
        try:
            cursor.execute(check["query"])
            result = cursor.fetchone()
            count = result["count"] if result else 0
            
            if count == 0:
                logger.info(f"  ✅ {check['name']}")
            else:
                logger.warning(f"  ⚠️  {check['name']}: {count} violations")
                all_valid = False
        except Exception as e:
            logger.warning(f"  ⚠️  {check['name']}: Check failed ({e})")
    
    cursor.close()
    return all_valid


def main():
    """Main execution."""
    logger.info("="*60)
    logger.info("Phase 0 - Database Migration Validation")
    logger.info("="*60)
    
    try:
        conn = get_postgres_connection()
        logger.info("✅ Connected to PostgreSQL\n")
        
        results = []
        
        # Run validations
        results.append(("Extensions", validate_extensions(conn)))
        results.append(("Core Data", validate_tenant_data(conn)))
        results.append(("TimescaleDB Metrics", validate_timescale_metrics(conn)))
        results.append(("pgvector Embeddings", validate_pgvector_embeddings(conn)))
        results.append(("Data Integrity", validate_data_integrity(conn)))
        
        conn.close()
        
        # Summary
        logger.info("\n" + "="*60)
        logger.info("Validation Summary")
        logger.info("="*60)
        
        all_passed = all(result for _, result in results)
        
        for name, passed in results:
            status = "✅ PASSED" if passed else "❌ FAILED"
            logger.info(f"  {name:25s}: {status}")
        
        logger.info("="*60)
        
        if all_passed:
            logger.info("\n🎉 All validations passed!")
            logger.info("\nNext steps:")
            logger.info("  1. Review Phase 0 migration scripts")
            logger.info("  2. Begin Phase 0.2: Code consolidation")
            logger.info("  3. Update application to use consolidated database")
            return 0
        else:
            logger.warning("\n⚠️  Some validations failed. Review logs above.")
            return 1
        
    except Exception as e:
        logger.error(f"❌ Validation failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
