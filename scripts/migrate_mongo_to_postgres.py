#!/usr/bin/env python3
"""
MongoDB to PostgreSQL Migration Script

Migrates tenant data from MongoDB to PostgreSQL for SMB tier deployments.
Supports both full migration and incremental sync.

Usage:
    # Dry run (no changes)
    python migrate_mongo_to_postgres.py --dry-run
    
    # Migrate specific tenant
    python migrate_mongo_to_postgres.py --tenant-id <tenant_id>
    
    # Full migration
    python migrate_mongo_to_postgres.py --all
    
    # Verify migration
    python migrate_mongo_to_postgres.py --verify --tenant-id <tenant_id>
"""

import argparse
import logging
import sys
from pathlib import Path
from typing import Dict, List, Optional

# Add packages to path
sys.path.insert(0, str(Path(__file__).parent.parent / "packages"))

from pymongo import MongoClient
import psycopg2
from psycopg2.extras import Json, RealDictCursor
import json
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)


class MongoToPostgresMigration:
    """MongoDB to PostgreSQL migration handler."""
    
    def __init__(self, mongo_uri: str, postgres_config: Dict[str, str], dry_run: bool = False):
        self.mongo_uri = mongo_uri
        self.postgres_config = postgres_config
        self.dry_run = dry_run
        
        self.mongo_client = None
        self.mongo_db = None
        self.pg_conn = None
        
        self.stats = {
            "tenants": {"processed": 0, "succeeded": 0, "failed": 0},
            "users": {"processed": 0, "succeeded": 0, "failed": 0},
            "projects": {"processed": 0, "succeeded": 0, "failed": 0},
            "runs": {"processed": 0, "succeeded": 0, "failed": 0},
            "connectors": {"processed": 0, "succeeded": 0, "failed": 0}
        }
    
    def connect(self):
        """Establish database connections."""
        logger.info("Connecting to MongoDB...")
        self.mongo_client = MongoClient(self.mongo_uri)
        self.mongo_db = self.mongo_client.get_default_database()
        
        logger.info("Connecting to PostgreSQL...")
        self.pg_conn = psycopg2.connect(**self.postgres_config)
        self.pg_conn.autocommit = False  # Use transactions
        
        logger.info("Database connections established")
    
    def disconnect(self):
        """Close database connections."""
        if self.mongo_client:
            self.mongo_client.close()
        if self.pg_conn:
            self.pg_conn.close()
    
    def migrate_tenant(self, tenant_id: str) -> bool:
        """Migrate a single tenant and all related data."""
        logger.info(f"Migrating tenant: {tenant_id}")
        
        try:
            # Start transaction
            if not self.dry_run:
                self.pg_conn.rollback()  # Clear any pending transaction
            
            # Migrate tenant
            tenant = self.mongo_db.tenants.find_one({"tenant_id": tenant_id})
            if not tenant:
                logger.error(f"Tenant {tenant_id} not found in MongoDB")
                return False
            
            self._migrate_tenant_record(tenant)
            
            # Migrate users
            users = list(self.mongo_db.users.find({"tenant_id": tenant_id}))
            for user in users:
                self._migrate_user_record(user)
            
            # Migrate projects
            projects = list(self.mongo_db.projects.find({"tenant_id": tenant_id}))
            for project in projects:
                self._migrate_project_record(project)
            
            # Migrate runs
            runs = list(self.mongo_db.runs.find({"tenant_id": tenant_id}))
            for run in runs:
                self._migrate_run_record(run)
            
            # Migrate connectors
            connectors = list(self.mongo_db.connectors.find({"tenant_id": tenant_id}))
            for connector in connectors:
                self._migrate_connector_record(connector)
            
            # Commit transaction
            if not self.dry_run:
                self.pg_conn.commit()
                logger.info(f"Successfully migrated tenant {tenant_id}")
            else:
                self.pg_conn.rollback()
                logger.info(f"[DRY RUN] Would migrate tenant {tenant_id}")
            
            return True
            
        except Exception as exc:
            logger.error(f"Error migrating tenant {tenant_id}: {exc}", exc_info=True)
            if not self.dry_run:
                self.pg_conn.rollback()
            self.stats["tenants"]["failed"] += 1
            return False
    
    def _migrate_tenant_record(self, tenant: Dict):
        """Migrate tenant record."""
        with self.pg_conn.cursor() as cur:
            sql = """
                INSERT INTO tenants.tenants (
                    tenant_id, name, owner_email, plan_tier, api_token,
                    status, created_at, updated_at, metadata, limits, usage
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (tenant_id) DO UPDATE SET
                    name = EXCLUDED.name,
                    owner_email = EXCLUDED.owner_email,
                    plan_tier = EXCLUDED.plan_tier,
                    updated_at = EXCLUDED.updated_at
            """
            
            cur.execute(sql, (
                tenant.get("tenant_id"),
                tenant.get("name"),
                tenant.get("owner_email"),
                tenant.get("plan_tier", "free"),
                tenant.get("api_token"),
                tenant.get("status", "active"),
                tenant.get("created_at", datetime.utcnow()),
                tenant.get("updated_at", datetime.utcnow()),
                Json(tenant.get("metadata", {})),
                Json(tenant.get("limits", {})),
                Json(tenant.get("usage", {}))
            ))
        
        self.stats["tenants"]["processed"] += 1
        self.stats["tenants"]["succeeded"] += 1
    
    def _migrate_user_record(self, user: Dict):
        """Migrate user record."""
        with self.pg_conn.cursor() as cur:
            sql = """
                INSERT INTO tenants.users (
                    user_id, tenant_id, email, full_name, password_hash,
                    roles, status, last_login, created_at, updated_at, metadata
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (user_id) DO UPDATE SET
                    email = EXCLUDED.email,
                    full_name = EXCLUDED.full_name,
                    updated_at = EXCLUDED.updated_at
            """
            
            cur.execute(sql, (
                user.get("user_id"),
                user.get("tenant_id"),
                user.get("email"),
                user.get("full_name"),
                user.get("password_hash"),
                user.get("roles", ["member"]),
                user.get("status", "active"),
                user.get("last_login"),
                user.get("created_at", datetime.utcnow()),
                user.get("updated_at", datetime.utcnow()),
                Json(user.get("metadata", {}))
            ))
        
        self.stats["users"]["processed"] += 1
        self.stats["users"]["succeeded"] += 1
    
    def _migrate_project_record(self, project: Dict):
        """Migrate project record."""
        with self.pg_conn.cursor() as cur:
            sql = """
                INSERT INTO tenants.projects (
                    project_id, tenant_id, name, description, archetype,
                    owner_id, status, created_at, updated_at, metadata
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (project_id) DO UPDATE SET
                    name = EXCLUDED.name,
                    description = EXCLUDED.description,
                    updated_at = EXCLUDED.updated_at
            """
            
            cur.execute(sql, (
                project.get("project_id"),
                project.get("tenant_id"),
                project.get("name"),
                project.get("description"),
                project.get("archetype"),
                project.get("owner_id"),
                project.get("status", "active"),
                project.get("created_at", datetime.utcnow()),
                project.get("updated_at", datetime.utcnow()),
                Json(project.get("metadata", {}))
            ))
        
        self.stats["projects"]["processed"] += 1
        self.stats["projects"]["succeeded"] += 1
    
    def _migrate_run_record(self, run: Dict):
        """Migrate run record."""
        with self.pg_conn.cursor() as cur:
            sql = """
                INSERT INTO runs.runs (
                    run_id, tenant_id, project_id, user_id, status,
                    ops_payload, solution_pack, started_at, completed_at,
                    duration_seconds, error_message, created_at, updated_at, metadata
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (run_id) DO UPDATE SET
                    status = EXCLUDED.status,
                    solution_pack = EXCLUDED.solution_pack,
                    updated_at = EXCLUDED.updated_at
            """
            
            cur.execute(sql, (
                run.get("run_id"),
                run.get("tenant_id"),
                run.get("project_id"),
                run.get("user_id"),
                run.get("status", "pending"),
                Json(run.get("ops_payload", {})),
                Json(run.get("solution_pack")) if run.get("solution_pack") else None,
                run.get("started_at"),
                run.get("completed_at"),
                run.get("duration_seconds"),
                run.get("error_message"),
                run.get("created_at", datetime.utcnow()),
                run.get("updated_at", datetime.utcnow()),
                Json(run.get("metadata", {}))
            ))
        
        self.stats["runs"]["processed"] += 1
        self.stats["runs"]["succeeded"] += 1
    
    def _migrate_connector_record(self, connector: Dict):
        """Migrate connector record."""
        with self.pg_conn.cursor() as cur:
            sql = """
                INSERT INTO connectors.connectors (
                    connector_id, tenant_id, connector_type, display_name,
                    config_encrypted, status, last_sync, created_at, updated_at, metadata
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (connector_id) DO UPDATE SET
                    display_name = EXCLUDED.display_name,
                    status = EXCLUDED.status,
                    updated_at = EXCLUDED.updated_at
            """
            
            # Note: config_encrypted needs proper encryption handling
            config_encrypted = None
            if connector.get("config"):
                # TODO: Implement proper encryption
                config_encrypted = json.dumps(connector["config"]).encode()
            
            cur.execute(sql, (
                connector.get("connector_id"),
                connector.get("tenant_id"),
                connector.get("connector_type"),
                connector.get("display_name"),
                config_encrypted,
                connector.get("status", "active"),
                connector.get("last_sync"),
                connector.get("created_at", datetime.utcnow()),
                connector.get("updated_at", datetime.utcnow()),
                Json(connector.get("metadata", {}))
            ))
        
        self.stats["connectors"]["processed"] += 1
        self.stats["connectors"]["succeeded"] += 1
    
    def migrate_all_tenants(self) -> None:
        """Migrate all tenants from MongoDB to PostgreSQL."""
        logger.info("Starting full migration...")
        
        tenants = list(self.mongo_db.tenants.find({}))
        total = len(tenants)
        
        logger.info(f"Found {total} tenants to migrate")
        
        for idx, tenant in enumerate(tenants, 1):
            tenant_id = tenant["tenant_id"]
            logger.info(f"[{idx}/{total}] Migrating {tenant_id}...")
            self.migrate_tenant(tenant_id)
        
        self._print_stats()
    
    def verify_migration(self, tenant_id: str) -> bool:
        """Verify that tenant data was migrated correctly."""
        logger.info(f"Verifying migration for tenant: {tenant_id}")
        
        # Compare counts
        mongo_users = self.mongo_db.users.count_documents({"tenant_id": tenant_id})
        mongo_projects = self.mongo_db.projects.count_documents({"tenant_id": tenant_id})
        mongo_runs = self.mongo_db.runs.count_documents({"tenant_id": tenant_id})
        
        with self.pg_conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM tenants.users WHERE tenant_id = %s", (tenant_id,))
            pg_users = cur.fetchone()[0]
            
            cur.execute("SELECT COUNT(*) FROM tenants.projects WHERE tenant_id = %s", (tenant_id,))
            pg_projects = cur.fetchone()[0]
            
            cur.execute("SELECT COUNT(*) FROM runs.runs WHERE tenant_id = %s", (tenant_id,))
            pg_runs = cur.fetchone()[0]
        
        logger.info(f"MongoDB -> PostgreSQL counts:")
        logger.info(f"  Users: {mongo_users} -> {pg_users}")
        logger.info(f"  Projects: {mongo_projects} -> {pg_projects}")
        logger.info(f"  Runs: {mongo_runs} -> {pg_runs}")
        
        verified = (
            mongo_users == pg_users and
            mongo_projects == pg_projects and
            mongo_runs == pg_runs
        )
        
        if verified:
            logger.info("✓ Migration verified successfully")
        else:
            logger.warning("✗ Migration verification failed - counts don't match")
        
        return verified
    
    def _print_stats(self):
        """Print migration statistics."""
        logger.info("=" * 60)
        logger.info("Migration Statistics:")
        logger.info("=" * 60)
        
        for entity, stats in self.stats.items():
            logger.info(f"{entity.capitalize()}:")
            logger.info(f"  Processed: {stats['processed']}")
            logger.info(f"  Succeeded: {stats['succeeded']}")
            logger.info(f"  Failed: {stats['failed']}")
        
        logger.info("=" * 60)


def main():
    parser = argparse.ArgumentParser(description="Migrate MongoDB data to PostgreSQL")
    parser.add_argument("--mongo-uri", default="mongodb://localhost:27017/dyocense",
                        help="MongoDB connection URI")
    parser.add_argument("--postgres-host", default="localhost", help="PostgreSQL host")
    parser.add_argument("--postgres-port", default="5432", help="PostgreSQL port")
    parser.add_argument("--postgres-db", default="dyocense", help="PostgreSQL database")
    parser.add_argument("--postgres-user", default="dyocense", help="PostgreSQL user")
    parser.add_argument("--postgres-password", required=True, help="PostgreSQL password")
    
    parser.add_argument("--tenant-id", help="Migrate specific tenant")
    parser.add_argument("--all", action="store_true", help="Migrate all tenants")
    parser.add_argument("--verify", action="store_true", help="Verify migration")
    parser.add_argument("--dry-run", action="store_true", help="Dry run (no changes)")
    
    args = parser.parse_args()
    
    postgres_config = {
        "host": args.postgres_host,
        "port": args.postgres_port,
        "database": args.postgres_db,
        "user": args.postgres_user,
        "password": args.postgres_password
    }
    
    migrator = MongoToPostgresMigration(
        mongo_uri=args.mongo_uri,
        postgres_config=postgres_config,
        dry_run=args.dry_run
    )
    
    try:
        migrator.connect()
        
        if args.verify:
            if not args.tenant_id:
                logger.error("--tenant-id required for verification")
                sys.exit(1)
            migrator.verify_migration(args.tenant_id)
        
        elif args.all:
            migrator.migrate_all_tenants()
        
        elif args.tenant_id:
            success = migrator.migrate_tenant(args.tenant_id)
            sys.exit(0 if success else 1)
        
        else:
            parser.print_help()
    
    finally:
        migrator.disconnect()


if __name__ == "__main__":
    main()
