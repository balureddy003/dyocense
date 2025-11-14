# Project Cleanup Plan - v4.0 Monolith Alignment

## Overview

This document outlines the cleanup needed to align the project structure with v4.0 monolith architecture.

---

## 1. Files/Folders to DELETE

### 1.1 Old Environment Files

- ✅ `.env.old` - Outdated environment configuration

### 1.2 Deprecated Infrastructure (Old Microservices)

- ❌ `infra/docker-compose/` - Old multi-service Docker setup (replaced by `docker-compose.smb.yml`)
- ❌ `infra/k8s/` - Kubernetes configs for microservices (not needed for monolith)

### 1.3 Service-Level Requirements (Consolidated)

- ❌ `services/kernel/requirements.txt` - Consolidated into `requirements-v4.txt`
- ❌ `services/keystone_proxy/requirements.txt` - Consolidated into `requirements-v4.txt`

### 1.4 Deprecated Services (Not in Unified Kernel)

Based on `services/kernel/main.py`, these services are **NOT** loaded:

- ❌ `services/agent_shell/` - Demo service, not in production kernel
- ❌ `services/keystone_proxy/` - Deprecated proxy service
- ❌ `services/notifications/` - Not mounted in kernel
- ❌ `services/scenario/` - Not mounted in kernel

### 1.5 Old Migration Scripts (Keep Only Phase 0)

- ❌ `scripts/migrate_connector_data_chunks.py` - Old migration
- ❌ `scripts/migrate_connector_data_table.py` - Old migration
- ❌ `scripts/run_migration.py` - Generic, replaced by Phase 0 scripts
- ⚠️  `scripts/migrate_mongo_to_postgres.py` - Keep for now, may need updates

### 1.6 Test Scripts (To Organize)

Move to `tests/integration/`:

- `scripts/test_*.py` files (15 test scripts in `/scripts`)

### 1.7 Old Demo Scripts

- ❌ `scripts/phase3_demo.py` - Outdated demo
- ❌ `scripts/capture_trip_planner.py` - Example/demo script

---

## 2. Files/Folders to KEEP

### 2.1 Essential Scripts

- ✅ `scripts/phase0_*.py` - Phase 0 migration scripts
- ✅ `scripts/quickstart_smb.sh` - SMB deployment script
- ✅ `scripts/ingest_dataset.py` - Data ingestion
- ✅ `scripts/load_csv_data_for_tenant.py` - CSV loading
- ✅ `scripts/seed_cyclonerake_*.py` - Tenant seeding
- ✅ `scripts/create_test_tenant_cyclonerake.py` - Test tenant creation
- ✅ `scripts/evaluate_*.py` - Evaluation tools
- ✅ `scripts/benchmark_compiler_retrieval.py` - Performance testing
- ✅ `scripts/add_connector_columns.py` - Database migration utility
- ✅ `scripts/validate_ops.py` - OPS validation

### 2.2 Active Services (Mounted in Kernel)

From `services/kernel/main.py`:

- ✅ `services/accounts/` - Account management
- ✅ `services/chat/` - Chat interface
- ✅ `services/compiler/` - OPS compiler
- ✅ `services/forecast/` - Forecasting
- ✅ `services/policy/` - Policy evaluation
- ✅ `services/optimiser/` - Optimization
- ✅ `services/diagnostician/` - Diagnostics
- ✅ `services/explainer/` - Explanations
- ✅ `services/evidence/` - Evidence tracking
- ✅ `services/marketplace/` - Marketplace
- ✅ `services/orchestrator/` - Orchestration
- ✅ `services/plan/` - Planning
- ✅ `services/analyze/` - Analytics
- ✅ `services/smb_gateway/` - SMB API (primary service)
- ✅ `services/connectors/` - Data connectors (feature-flagged)
- ✅ `services/kernel/` - Unified kernel

### 2.3 Infrastructure

- ✅ `docker-compose.smb.yml` - v4.0 unified deployment
- ✅ `Dockerfile.unified` - Monolith container
- ✅ `infra/postgres/` - PostgreSQL schema
- ⚠️  `infra/README.md` - Update to reflect v4.0 only

### 2.4 Documentation

- ✅ `docs/Refactoring-Guide.md` - Phase 0 implementation guide
- ✅ `docs/PHASE0-IMPLEMENTATION.md` - Phase 0 quick start
- ✅ All architecture docs (update references)

---

## 3. Reorganization Needed

### 3.1 Create Test Directory Structure

```
tests/
├── unit/
├── integration/           # Move scripts/test_*.py here
│   ├── test_multi_agent.py
│   ├── test_conversational_coach.py
│   ├── test_connector_data_flow.py
│   ├── test_csv_ingestion.py
│   ├── test_chunk_ingestion.py
│   ├── test_restaurant_e2e.py
│   ├── test_background_jobs.py
│   ├── test_kernel_imports.py
│   └── test_multi_agent_data_awareness.py
└── e2e/
    └── test_phase2_e2e.sh
```

### 3.2 Scripts Organization

```
scripts/
├── migration/             # Phase 0 migration scripts
│   ├── phase0_setup_postgres_extensions.py
│   ├── phase0_migrate_influxdb.py
│   ├── phase0_migrate_pinecone.py
│   ├── phase0_validate_migration.py
│   └── migrate_mongo_to_postgres.py
├── data/                  # Data ingestion
│   ├── ingest_dataset.py
│   ├── load_csv_data_for_tenant.py
│   └── add_connector_columns.py
├── seed/                  # Tenant/data seeding
│   ├── create_test_tenant_cyclonerake.py
│   ├── seed_cyclonerake_goals.py
│   └── seed_cyclonerake_tasks.py
├── evaluation/            # Evaluation tools
│   ├── evaluate_compiler.py
│   ├── evaluate_plan_quality.py
│   └── benchmark_compiler_retrieval.py
├── deployment/            # Deployment scripts
│   ├── quickstart_smb.sh
│   ├── start_connector_service.sh
│   └── kind_bootstrap.sh
└── utils/                 # Utilities
    └── validate_ops.py
```

### 3.3 Update Dependencies

- ✅ Create root-level `requirements.txt` symlink to `requirements-v4.txt`
- ❌ Remove service-level `requirements.txt` files

---

## 4. Documentation Updates Needed

### 4.1 Update Architecture Docs

Files to update with v4.0 references:

- `docs/Service-Architecture.md` - Update to monolith architecture
- `docs/Technology Stack Selection.md` - Remove microservices references
- `docs/Implementation-Roadmap.md` - Mark Phase 0 complete
- `infra/README.md` - Update deployment instructions
- `services/README.md` - Clarify monolith vs mounted services

### 4.2 Remove Outdated References

- Remove references to:
  - Separate microservice deployment
  - Kubernetes deployment
  - Service-to-service HTTP calls
  - Multiple databases (MongoDB, InfluxDB, Pinecone, Neo4j)
  - Kafka/NATS for inter-service communication

### 4.3 Add v4.0 Documentation

- ✅ Monolith architecture diagram
- ✅ Single PostgreSQL with extensions guide
- ✅ FastAPI service mounting pattern
- ✅ RLS multi-tenancy implementation

---

## 5. Code Updates Required

### 5.1 Remove Inter-Service HTTP Clients

Services should use direct Python imports, not HTTP:

- `services/smb_gateway/optimization_tools.py` - Remove HTTP client for optimizer
- Update all `httpx.AsyncClient` calls between services

### 5.2 Consolidate Common Utilities

Move duplicated code to `packages/kernel_common/`:

- Shared models
- Common middleware
- Utility functions

### 5.3 Update Service README Files

Update each service's README to reflect:

- Mounted in unified kernel (not standalone)
- No separate deployment
- PostgreSQL-only backend

---

## 6. Cleanup Commands

### Phase 1: Backup

```bash
# Create backup branch
git checkout -b backup/pre-v4-cleanup

# Create archive of old files
tar -czf ~/dyocense-backup-$(date +%Y%m%d).tar.gz \
  .env.old \
  infra/docker-compose/ \
  infra/k8s/ \
  services/agent_shell/ \
  services/keystone_proxy/ \
  services/notifications/ \
  services/scenario/
```

### Phase 2: Remove Deprecated Services

```bash
# Delete deprecated services
rm -rf services/agent_shell/
rm -rf services/keystone_proxy/
rm -rf services/notifications/
rm -rf services/scenario/

# Delete old infrastructure
rm -rf infra/docker-compose/
rm -rf infra/k8s/
```

### Phase 3: Remove Old Configs

```bash
# Delete old environment files
rm .env.old

# Delete service-level requirements
rm services/kernel/requirements.txt
rm services/keystone_proxy/requirements.txt
```

### Phase 4: Reorganize Scripts

```bash
# Create new directory structure
mkdir -p scripts/{migration,data,seed,evaluation,deployment,utils}
mkdir -p tests/integration tests/e2e

# Move migration scripts
mv scripts/phase0_*.py scripts/migration/
mv scripts/migrate_mongo_to_postgres.py scripts/migration/

# Move data scripts
mv scripts/ingest_dataset.py scripts/data/
mv scripts/load_csv_data_for_tenant.py scripts/data/
mv scripts/add_connector_columns.py scripts/data/

# Move seed scripts
mv scripts/create_test_tenant_cyclonerake.py scripts/seed/
mv scripts/seed_cyclonerake_*.py scripts/seed/

# Move evaluation scripts
mv scripts/evaluate_*.py scripts/evaluation/
mv scripts/benchmark_compiler_retrieval.py scripts/evaluation/

# Move deployment scripts
mv scripts/quickstart_smb.sh scripts/deployment/
mv scripts/start_connector_service.sh scripts/deployment/
mv scripts/kind_bootstrap.sh scripts/deployment/

# Move utils
mv scripts/validate_ops.py scripts/utils/

# Move tests
mv scripts/test_*.py tests/integration/
mv scripts/test_phase2_e2e.sh tests/e2e/

# Delete old demo scripts
rm scripts/phase3_demo.py
rm scripts/capture_trip_planner.py
rm scripts/migrate_connector_data_chunks.py
rm scripts/migrate_connector_data_table.py
rm scripts/run_migration.py
```

### Phase 5: Create Symlink for Requirements

```bash
# Create symlink at root
ln -s requirements-v4.txt requirements.txt
```

---

## 7. Validation After Cleanup

### 7.1 Test Unified Kernel

```bash
# Start kernel
docker-compose -f docker-compose.smb.yml up kernel

# Test health endpoint
curl http://localhost:8001/health

# Check mounted services
curl http://localhost:8001/openapi.json | jq '.paths | keys'
```

### 7.2 Run Tests

```bash
# Run unit tests
pytest tests/unit/

# Run integration tests
pytest tests/integration/

# Run e2e tests
bash tests/e2e/test_phase2_e2e.sh
```

### 7.3 Validate Dependencies

```bash
# Install consolidated requirements
pip install -r requirements-v4.txt

# Check for missing imports
python -c "from services.kernel.main import app; print('✅ Kernel imports OK')"
```

---

## 8. Expected Outcomes

After cleanup:

- ✅ **-4 deprecated services removed** (agent_shell, keystone_proxy, notifications, scenario)
- ✅ **-2 infrastructure directories removed** (docker-compose/, k8s/)
- ✅ **-6 old scripts removed** (migration/demo scripts)
- ✅ **+Organized script structure** (6 subdirectories)
- ✅ **+Organized test structure** (unit/integration/e2e)
- ✅ **Single requirements.txt** (symlink to requirements-v4.txt)
- ✅ **Clearer project structure** aligned with v4.0 monolith

---

## 9. Rollback Plan

If issues arise:

```bash
# Restore from backup branch
git checkout backup/pre-v4-cleanup

# Or restore from archive
tar -xzf ~/dyocense-backup-YYYYMMDD.tar.gz
```

---

## Next Steps

1. Review this cleanup plan
2. Execute Phase 1 (Backup)
3. Execute Phase 2-5 (Cleanup)
4. Execute validation tests
5. Update documentation references
6. Commit changes to `feature/v4-cleanup` branch
