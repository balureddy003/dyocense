#!/usr/bin/env python3
"""
Phase 0 - Step 3: Migrate Pinecone to pgvector

Migrates vector embeddings from Pinecone to PostgreSQL pgvector.

Usage:
    # Dry run
    python scripts/phase0_migrate_pinecone.py --dry-run
    
    # Migrate all vectors
    python scripts/phase0_migrate_pinecone.py
    
    # Migrate specific namespace
    python scripts/phase0_migrate_pinecone.py --namespace <namespace>
"""

import os
import sys
import argparse
import logging
from pathlib import Path

import psycopg2
from psycopg2.extras import execute_batch
import json

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)


class PineconeToPgVectorMigration:
    """Migrate Pinecone vectors to PostgreSQL pgvector."""
    
    def __init__(self, postgres_config: dict, dry_run: bool = False):
        self.postgres_config = postgres_config
        self.dry_run = dry_run
        self.pg_conn = None
        self.pinecone_index = None
        
        self.stats = {
            "total_vectors": 0,
            "migrated": 0,
            "failed": 0
        }
    
    def connect(self):
        """Establish database connections."""
        logger.info("Connecting to PostgreSQL...")
        self.pg_conn = psycopg2.connect(**self.postgres_config)
        
        # Check if Pinecone client is available
        try:
            import pinecone
            
            api_key = os.getenv("PINECONE_API_KEY")
            environment = os.getenv("PINECONE_ENVIRONMENT", "us-west1-gcp")
            index_name = os.getenv("PINECONE_INDEX", "dyocense-embeddings")
            
            if not api_key:
                logger.warning("PINECONE_API_KEY not set, will skip Pinecone migration")
                self.pinecone_index = None
                return
            
            logger.info(f"Connecting to Pinecone index: {index_name}")
            pinecone.init(api_key=api_key, environment=environment)
            self.pinecone_index = pinecone.Index(index_name)
            
            # Get stats
            stats = self.pinecone_index.describe_index_stats()
            self.stats["total_vectors"] = stats.get("total_vector_count", 0)
            
            logger.info(f"✅ Connected to Pinecone (total vectors: {self.stats['total_vectors']})")
            
        except ImportError:
            logger.warning("pinecone-client not installed, skipping Pinecone migration")
            self.pinecone_index = None
        except Exception as e:
            logger.error(f"Failed to connect to Pinecone: {e}")
            self.pinecone_index = None
    
    def disconnect(self):
        """Close database connections."""
        if self.pg_conn:
            self.pg_conn.close()
    
    def migrate_vectors(self, namespace: str = ""):
        """Migrate vectors from Pinecone to pgvector."""
        
        if not self.pinecone_index:
            logger.info("No Pinecone connection, skipping migration")
            return
        
        logger.info(f"Migrating vectors from namespace: '{namespace}'...")
        
        cursor = self.pg_conn.cursor()
        
        # Fetch vector IDs (Pinecone requires fetching by IDs)
        stats = self.pinecone_index.describe_index_stats()
        namespaces_data = stats.get("namespaces", {})
        
        if namespace:
            if namespace not in namespaces_data:
                logger.warning(f"Namespace '{namespace}' not found in Pinecone")
                return
            vector_count = namespaces_data[namespace]["vector_count"]
        else:
            # Use default namespace
            vector_count = namespaces_data.get("", {}).get("vector_count", 0)
        
        logger.info(f"Found {vector_count} vectors to migrate")
        
        # Since Pinecone doesn't provide a direct list API, we'll use query with dummy vector
        # This is a workaround - in production, you'd track vector IDs separately
        logger.warning("⚠️  Pinecone migration requires vector IDs. Using query-based approach...")
        
        # Query all vectors using a dummy vector
        try:
            # Get sample vectors using query
            query_results = self.pinecone_index.query(
                vector=[0.0] * 1536,  # Dummy vector (adjust dimension as needed)
                top_k=10000,  # Pinecone max
                include_values=True,
                include_metadata=True,
                namespace=namespace
            )
            
            batch_data = []
            
            for match in query_results.get("matches", []):
                vector_id = match["id"]
                vector_values = match.get("values", [])
                metadata = match.get("metadata", {})
                
                data = {
                    "embedding_id": vector_id,
                    "tenant_id": metadata.get("tenant_id", "unknown"),
                    "content": metadata.get("content", ""),
                    "embedding": vector_values,
                    "metadata": json.dumps(metadata)
                }
                
                batch_data.append(data)
                
                # Batch insert every 100 vectors
                if len(batch_data) >= 100:
                    self._insert_batch(cursor, batch_data)
                    batch_data = []
            
            # Insert remaining vectors
            if batch_data:
                self._insert_batch(cursor, batch_data)
            
            if not self.dry_run:
                self.pg_conn.commit()
            else:
                self.pg_conn.rollback()
            
            cursor.close()
            
            logger.info(f"\n{'='*60}")
            logger.info(f"Migration Statistics:")
            logger.info(f"{'='*60}")
            logger.info(f"  Total vectors: {self.stats['total_vectors']}")
            logger.info(f"  Migrated: {self.stats['migrated']}")
            logger.info(f"  Failed: {self.stats['failed']}")
            logger.info(f"{'='*60}\n")
            
            logger.warning("⚠️  Note: This migration may not capture all vectors.")
            logger.warning("⚠️  Consider using Pinecone's export feature for full migration.")
            
        except Exception as e:
            logger.error(f"Migration failed: {e}")
            self.pg_conn.rollback()
            raise
    
    def _insert_batch(self, cursor, batch_data):
        """Insert batch of embeddings."""
        
        if self.dry_run:
            self.stats["migrated"] += len(batch_data)
            logger.info(f"[DRY RUN] Would insert {len(batch_data)} vectors")
            return
        
        try:
            execute_batch(cursor, """
                INSERT INTO embeddings (embedding_id, tenant_id, content, embedding, metadata)
                VALUES (%(embedding_id)s, %(tenant_id)s, %(content)s, %(embedding)s::vector, %(metadata)s::jsonb)
                ON CONFLICT (embedding_id) DO UPDATE 
                SET embedding = EXCLUDED.embedding, metadata = EXCLUDED.metadata
            """, batch_data, page_size=100)
            
            self.stats["migrated"] += len(batch_data)
            logger.info(f"✅ Inserted {len(batch_data)} vectors (total: {self.stats['migrated']})")
            
        except Exception as e:
            logger.error(f"Batch insert failed: {e}")
            self.stats["failed"] += len(batch_data)


def main():
    """Main execution."""
    parser = argparse.ArgumentParser(description="Migrate Pinecone to pgvector")
    parser.add_argument("--dry-run", action="store_true", help="Dry run (no changes)")
    parser.add_argument("--namespace", default="", help="Pinecone namespace to migrate")
    
    args = parser.parse_args()
    
    logger.info("="*60)
    logger.info("Phase 0 - Pinecone to pgvector Migration")
    logger.info("="*60)
    if args.dry_run:
        logger.info("⚠️  DRY RUN MODE - No changes will be made")
    logger.info("")
    
    postgres_config = {
        "host": os.getenv("POSTGRES_HOST", "localhost"),
        "port": int(os.getenv("POSTGRES_PORT", "5432")),
        "dbname": os.getenv("POSTGRES_DB", "dyocense"),
        "user": os.getenv("POSTGRES_USER", "dyocense"),
        "password": os.getenv("POSTGRES_PASSWORD", "pass@1234")
    }
    
    try:
        migration = PineconeToPgVectorMigration(postgres_config, dry_run=args.dry_run)
        migration.connect()
        migration.migrate_vectors(namespace=args.namespace)
        migration.disconnect()
        
        logger.info("\n✅ Migration complete!")
        logger.info("\nNext steps:")
        logger.info("  1. Verify migration: python scripts/phase0_validate_migration.py")
        logger.info("  2. Test vector search performance")
        logger.info("  3. Update application to use pgvector instead of Pinecone")
        
    except Exception as e:
        logger.error(f"❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
