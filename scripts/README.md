# Scripts Directory

Organized scripts for development, deployment, and maintenance.

## Directory Structure

### `migration/`

Database migration scripts for Phase 0 consolidation:

- `phase0_setup_postgres_extensions.py` - Install PostgreSQL extensions (pgvector, TimescaleDB, etc.)
- `phase0_migrate_influxdb.py` - Migrate InfluxDB metrics to TimescaleDB
- `phase0_migrate_pinecone.py` - Migrate Pinecone vectors to pgvector
- `phase0_validate_migration.py` - Validate migration completeness and data integrity
- `migrate_mongo_to_postgres.py` - MongoDB to PostgreSQL migration utility

### `data/`

Data ingestion and management scripts:

- `ingest_dataset.py` - Generic dataset ingestion
- `load_csv_data_for_tenant.py` - Load CSV data for specific tenant
- `add_connector_columns.py` - Database migration utility for connector schema

### `seed/`

Test data and tenant seeding scripts:

- `create_test_tenant_cyclonerake.py` - Create test tenant
- `seed_cyclonerake_goals.py` - Seed test goals
- `seed_cyclonerake_tasks.py` - Seed test tasks

### `evaluation/`

Performance and quality evaluation scripts:

- `evaluate_compiler.py` - Evaluate compiler performance
- `evaluate_plan_quality.py` - Evaluate planning quality
- `benchmark_compiler_retrieval.py` - Benchmark retrieval performance

### `deployment/`

Deployment and infrastructure scripts:

- `quickstart_smb.sh` - SMB quick start deployment
- `start_connector_service.sh` - Start connector service
- `kind_bootstrap.sh` - Kubernetes (kind) bootstrap

### `utils/`

Utility scripts:

- `validate_ops.py` - Validate OPS documents

## Usage

### Phase 0 Migration (Database Consolidation)

```bash
# 1. Setup PostgreSQL extensions
python scripts/migration/phase0_setup_postgres_extensions.py

# 2. Migrate InfluxDB to TimescaleDB (if applicable)
python scripts/migration/phase0_migrate_influxdb.py --dry-run
python scripts/migration/phase0_migrate_influxdb.py --days 90

# 3. Migrate Pinecone to pgvector (if applicable)
python scripts/migration/phase0_migrate_pinecone.py --dry-run
python scripts/migration/phase0_migrate_pinecone.py

# 4. Validate migration
python scripts/migration/phase0_validate_migration.py
```

### Data Ingestion

```bash
# Load CSV data for tenant
python scripts/data/load_csv_data_for_tenant.py \
  --tenant-id acme-corp \
  --csv-file data/inventory.csv

# Generic dataset ingestion
python scripts/data/ingest_dataset.py \
  --source-type csv \
  --source-path data/sales.csv
```

### Deployment

```bash
# Quick start SMB deployment
bash scripts/deployment/quickstart_smb.sh

# Start connector service
bash scripts/deployment/start_connector_service.sh
```

### Evaluation

```bash
# Evaluate compiler performance
python scripts/evaluation/evaluate_compiler.py

# Benchmark retrieval
python scripts/evaluation/benchmark_compiler_retrieval.py
```

## Dependencies

Most scripts require the v4.0 consolidated dependencies:

```bash
pip install -r requirements-v4.txt
```

## See Also

- `/docs/PHASE0-IMPLEMENTATION.md` - Phase 0 implementation guide
- `/docs/Refactoring-Guide.md` - Comprehensive refactoring guide
- `/CLEANUP_PLAN.md` - Project cleanup plan
