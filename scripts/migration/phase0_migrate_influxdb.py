#!/usr/bin/env python3
"""
Phase 0 - Step 2: Migrate InfluxDB to TimescaleDB

Migrates time-series metrics from InfluxDB to PostgreSQL TimescaleDB.

Usage:
    # Dry run
    python scripts/phase0_migrate_influxdb.py --dry-run
    
    # Migrate last 90 days
    python scripts/phase0_migrate_influxdb.py --days 90
    
    # Migrate specific tenant
    python scripts/phase0_migrate_influxdb.py --tenant-id <tenant_id>
"""

import os
import sys
import argparse
import logging
from pathlib import Path
from datetime import datetime, timedelta

import psycopg2
from psycopg2.extras import execute_batch
import json

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)


class InfluxToTimescaleMigration:
    """Migrate InfluxDB metrics to PostgreSQL TimescaleDB."""
    
    def __init__(self, postgres_config: dict, dry_run: bool = False):
        self.postgres_config = postgres_config
        self.dry_run = dry_run
        self.pg_conn = None
        self.influx_client = None
        
        self.stats = {
            "total_points": 0,
            "migrated": 0,
            "failed": 0,
            "skipped": 0
        }
    
    def connect(self):
        """Establish database connections."""
        logger.info("Connecting to PostgreSQL...")
        self.pg_conn = psycopg2.connect(**self.postgres_config)
        
        # Check if InfluxDB client is available
        try:
            from influxdb_client import InfluxDBClient
            
            influx_url = os.getenv("INFLUXDB_URL", "http://localhost:8086")
            influx_token = os.getenv("INFLUXDB_TOKEN")
            influx_org = os.getenv("INFLUXDB_ORG", "dyocense")
            
            if not influx_token:
                logger.warning("INFLUXDB_TOKEN not set, will skip InfluxDB migration")
                self.influx_client = None
                return
            
            logger.info(f"Connecting to InfluxDB at {influx_url}...")
            self.influx_client = InfluxDBClient(
                url=influx_url,
                token=influx_token,
                org=influx_org
            )
            logger.info("✅ Connected to InfluxDB")
            
        except ImportError:
            logger.warning("influxdb-client not installed, skipping InfluxDB migration")
            self.influx_client = None
    
    def disconnect(self):
        """Close database connections."""
        if self.pg_conn:
            self.pg_conn.close()
        if self.influx_client:
            self.influx_client.close()
    
    def migrate_metrics(self, days: int = 90, tenant_id: str = None):
        """Migrate metrics from InfluxDB to TimescaleDB."""
        
        if not self.influx_client:
            logger.info("No InfluxDB connection, skipping migration")
            return
        
        logger.info(f"Migrating metrics from last {days} days...")
        
        query_api = self.influx_client.query_api()
        
        # Build Flux query
        filter_clause = f'|> filter(fn: (r) => r.tenant_id == "{tenant_id}")' if tenant_id else ""
        
        query = f'''
        from(bucket: "dyocense")
            |> range(start: -{days}d)
            |> filter(fn: (r) => r._measurement == "business_metrics")
            {filter_clause}
        '''
        
        logger.info(f"Executing query: {query}")
        
        try:
            tables = query_api.query(query)
            
            cursor = self.pg_conn.cursor()
            batch_data = []
            
            for table in tables:
                for record in table.records:
                    self.stats["total_points"] += 1
                    
                    # Extract data
                    data = {
                        "time": record.get_time(),
                        "tenant_id": record.values.get("tenant_id", "unknown"),
                        "metric_type": record.get_field(),
                        "metric_value": float(record.get_value()),
                        "tags": json.dumps(record.values)
                    }
                    
                    batch_data.append(data)
                    
                    # Batch insert every 1000 records
                    if len(batch_data) >= 1000:
                        self._insert_batch(cursor, batch_data)
                        batch_data = []
            
            # Insert remaining records
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
            logger.info(f"  Total points: {self.stats['total_points']}")
            logger.info(f"  Migrated: {self.stats['migrated']}")
            logger.info(f"  Failed: {self.stats['failed']}")
            logger.info(f"  Skipped: {self.stats['skipped']}")
            logger.info(f"{'='*60}\n")
            
        except Exception as e:
            logger.error(f"Migration failed: {e}")
            self.pg_conn.rollback()
            raise
    
    def _insert_batch(self, cursor, batch_data):
        """Insert batch of metrics."""
        
        if self.dry_run:
            self.stats["migrated"] += len(batch_data)
            logger.info(f"[DRY RUN] Would insert {len(batch_data)} records")
            return
        
        try:
            execute_batch(cursor, """
                INSERT INTO metrics (time, tenant_id, metric_type, metric_value, tags)
                VALUES (%(time)s, %(tenant_id)s, %(metric_type)s, %(metric_value)s, %(tags)s::jsonb)
                ON CONFLICT DO NOTHING
            """, batch_data, page_size=1000)
            
            self.stats["migrated"] += len(batch_data)
            logger.info(f"✅ Inserted {len(batch_data)} metrics (total: {self.stats['migrated']})")
            
        except Exception as e:
            logger.error(f"Batch insert failed: {e}")
            self.stats["failed"] += len(batch_data)


def main():
    """Main execution."""
    parser = argparse.ArgumentParser(description="Migrate InfluxDB to TimescaleDB")
    parser.add_argument("--dry-run", action="store_true", help="Dry run (no changes)")
    parser.add_argument("--days", type=int, default=90, help="Number of days to migrate")
    parser.add_argument("--tenant-id", help="Migrate specific tenant only")
    
    args = parser.parse_args()
    
    logger.info("="*60)
    logger.info("Phase 0 - InfluxDB to TimescaleDB Migration")
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
        migration = InfluxToTimescaleMigration(postgres_config, dry_run=args.dry_run)
        migration.connect()
        migration.migrate_metrics(days=args.days, tenant_id=args.tenant_id)
        migration.disconnect()
        
        logger.info("\n✅ Migration complete!")
        
    except Exception as e:
        logger.error(f"❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
