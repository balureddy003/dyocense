# Phase 0 Implementation Guide

## Quick Start

Phase 0 implements the foundation for v4.0 architecture transformation: consolidating 4 databases into PostgreSQL and preparing for service monolith.

### Prerequisites

```bash
# Install PostgreSQL 15+ with required extensions
brew install postgresql@15  # macOS
# OR
sudo apt-get install postgresql-15  # Ubuntu

# Install TimescaleDB extension
brew tap timescale/tap
brew install timescaledb

# Install pgvector extension
cd /tmp
git clone https://github.com/pgvector/pgvector.git
cd pgvector
make
make install  # May require sudo
```

### Phase 0.1: Database Consolidation (Week 1-2)

**Step 1: Set up PostgreSQL extensions**

```bash
# Set environment variables
export POSTGRES_HOST=localhost
export POSTGRES_PORT=5432
export POSTGRES_DB=dyocense
export POSTGRES_USER=dyocense
export POSTGRES_PASSWORD=pass@1234

# Run extension setup
python scripts/phase0_setup_postgres_extensions.py
```

**Expected output:**

```
✅ uuid-ossp installed successfully
✅ pgcrypto installed successfully
✅ pg_trgm installed successfully
✅ vector installed successfully
✅ timescaledb installed successfully
⚠️  age failed to install (optional)
⚠️  pg_cron failed to install (optional)
```

**Step 2: Migrate InfluxDB to TimescaleDB** (if applicable)

```bash
# Set InfluxDB credentials
export INFLUXDB_URL=http://localhost:8086
export INFLUXDB_TOKEN=your_influx_token
export INFLUXDB_ORG=dyocense

# Dry run first
python scripts/phase0_migrate_influxdb.py --dry-run --days 90

# Actual migration
python scripts/phase0_migrate_influxdb.py --days 90
```

**Step 3: Migrate Pinecone to pgvector** (if applicable)

```bash
# Set Pinecone credentials
export PINECONE_API_KEY=your_pinecone_key
export PINECONE_ENVIRONMENT=us-west1-gcp
export PINECONE_INDEX=dyocense-embeddings

# Dry run
python scripts/phase0_migrate_pinecone.py --dry-run

# Actual migration
python scripts/phase0_migrate_pinecone.py
```

**Step 4: Validate migration**

```bash
python scripts/phase0_validate_migration.py
```

**Expected output:**

```
Extensions           : ✅ PASSED
Core Data           : ✅ PASSED
TimescaleDB Metrics : ✅ PASSED
pgvector Embeddings : ✅ PASSED
Data Integrity      : ✅ PASSED

🎉 All validations passed!
```

---

### Phase 0.2: Code Consolidation (Week 3-4)

**Current Status:** The codebase already has a unified kernel approach in `services/kernel/main.py` that mounts multiple services.

**Goal:** Refactor to true monolith with direct function calls instead of FastAPI sub-apps.

**Step 1: Review current architecture**

```bash
# Check current service structure
ls -la services/

# Review kernel implementation
cat services/kernel/main.py
```

**Step 2: Consolidate services** (Implementation in progress)

The kernel currently loads services as separate FastAPI apps:

- `accounts_app`
- `chat_app`
- `compiler_app`
- `forecast_app`
- etc.

**Target:** Convert these to service modules with direct Python imports.

---

### Testing Phase 0

**Test PostgreSQL extensions:**

```bash
# Connect to PostgreSQL
psql -h localhost -U dyocense -d dyocense

# Check extensions
SELECT extname, extversion FROM pg_extension 
WHERE extname IN ('vector', 'timescaledb', 'uuid-ossp', 'pgcrypto');

# Test vector search
SELECT embedding <=> '[0.01, 0.02, ...]'::vector AS distance
FROM embeddings
ORDER BY embedding <=> '[0.01, 0.02, ...]'::vector
LIMIT 5;

# Test TimescaleDB
SELECT * FROM metrics 
WHERE time > NOW() - INTERVAL '7 days'
ORDER BY time DESC
LIMIT 10;
```

**Test unified kernel:**

```bash
# Start kernel
cd /Users/balu/Projects/dyocense
docker-compose -f docker-compose.smb.yml up kernel

# Test health endpoint
curl http://localhost:8001/health

# Test API endpoints
curl -H "Authorization: Bearer <token>" \
     http://localhost:8001/v1/tenants
```

---

### Rollback Procedure

If Phase 0 migration fails:

```bash
# 1. Stop new services
docker-compose -f docker-compose.smb.yml down

# 2. Restore PostgreSQL from backup
pg_restore -d dyocense /backups/postgres_before_migration.dump

# 3. Restart old services (if still running)
docker-compose -f docker-compose.old.yml up -d
```

---

### Success Metrics

Phase 0 is complete when:

- ✅ All PostgreSQL extensions installed and verified
- ✅ Time-series data accessible via TimescaleDB
- ✅ Vector search working with pgvector
- ✅ All tenant data migrated with 100% integrity
- ✅ Unified kernel serving all API requests
- ✅ Zero data loss confirmed by validation script

---

### Cost Savings Achieved

After Phase 0 completion:

| Component | Before | After | Savings |
|-----------|--------|-------|---------|
| **MongoDB** | $200/mo | $0 | $200/mo |
| **InfluxDB** | $200/mo | $0 | $200/mo |
| **Pinecone** | $200/mo | $0 | $200/mo |
| **Neo4j** | $500/mo | $0 | $500/mo |
| **PostgreSQL** | $50/mo | $50/mo | $0 |
| **Total** | **$1150/mo** | **$50/mo** | **$1100/mo** |

**Annual savings:** $13,200/year

---

### Next Steps

1. ✅ Complete Phase 0.1 (Database Migration)
2. ⏳ Complete Phase 0.2 (Code Consolidation)
3. ⏳ Phase 0.3 (Parallel Deployment)
4. ⏳ Phase 0.4 (Decommission Old Services)

See `/docs/Refactoring-Guide.md` for full implementation details.
