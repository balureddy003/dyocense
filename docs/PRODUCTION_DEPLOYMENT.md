# Production Deployment Guide

This guide walks through deploying Dyocense from development (in-memory stubs) to production with real external dependencies.

## Table of Contents

1. [Quick Start](#quick-start)
2. [Environment Configuration](#environment-configuration)
3. [Phase 1: MongoDB Setup](#phase-1-mongodb-setup)
4. [Phase 2: Keycloak Authentication](#phase-2-keycloak-authentication)
5. [Phase 3: LLM Services](#phase-3-llm-services)
6. [Phase 4: Graph & Vector Stores](#phase-4-graph--vector-stores)
7. [Health Checks & Monitoring](#health-checks--monitoring)
8. [Migration from Development](#migration-from-development)
9. [Troubleshooting](#troubleshooting)

---

## Quick Start

### Development Mode (Default)
```bash
# No external dependencies required
cp .env.example .env
python -m uvicorn services.kernel.main:app --port 8001

# All services use in-memory fallbacks
# Demo authentication: Bearer demo-tenant
```

### Production Mode
```bash
# Requires: MongoDB, Keycloak (optional: Neo4j, Qdrant, LLM)
cp .env.production .env
# Edit .env with your connection details
python -m uvicorn services.kernel.main:app --port 8001
```

---

## Environment Configuration

### Feature Flags

Control which real implementations are used vs stubs:

```bash
# Force all services to use in-memory stubs (dev/testing)
FORCE_INMEMORY_MODE=false

# Individual service toggles (default: true)
USE_MONGODB=true
USE_KEYCLOAK=true
USE_NEO4J=true
USE_QDRANT=true
USE_LLM=true

# Strict mode - fail if dependencies unavailable (production)
STRICT_MODE=false

# Optional features
ENABLE_TRANSACTIONS=true  # Requires MongoDB replica set
ENABLE_CACHING=true
ENABLE_METRICS=true
```

### Environment Settings

```bash
# Application
ENVIRONMENT=production  # development | staging | production
DEBUG=false
LOG_LEVEL=INFO  # DEBUG | INFO | WARNING | ERROR
```

---

## Phase 1: MongoDB Setup

### Option A: MongoDB Atlas (Recommended for Cloud)

1. **Create Cluster**
   ```
   - Go to https://cloud.mongodb.com
   - Create new cluster (M0 free tier for dev, M10+ for production)
   - Choose region close to your deployment
   - Note the connection string
   ```

2. **Configure Access**
   ```
   - Add IP whitelist (or 0.0.0.0/0 for testing)
   - Create database user with password
   - Note: username, password, database name
   ```

3. **Environment Variables**
   ```bash
   MONGO_URI=mongodb+srv://<username>:<password>@<cluster>.mongodb.net/?retryWrites=true&w=majority
   MONGO_DB_NAME=dyocense
   
   # Optional: Connection pool tuning
   MONGO_MAX_POOL_SIZE=50
   MONGO_MIN_POOL_SIZE=10
   ```

### Option B: Self-Hosted MongoDB

1. **Deploy MongoDB Replica Set** (recommended for transactions)
   ```bash
   # Docker Compose
   docker run -d \
     --name mongodb \
     -p 27017:27017 \
     -e MONGO_INITDB_ROOT_USERNAME=admin \
     -e MONGO_INITDB_ROOT_PASSWORD=password \
     mongo:6.0 --replSet rs0
   
   # Initialize replica set
   docker exec -it mongodb mongosh --eval "rs.initiate()"
   ```

2. **Environment Variables**
   ```bash
   MONGO_HOST=localhost
   MONGO_PORT=27017
   MONGO_USERNAME=admin
   MONGO_PASSWORD=password
   MONGO_AUTH_DB=admin
   MONGO_DB_NAME=dyocense
   MONGO_REPLICA_SET=rs0  # For transactions
   ```

### Create Indexes (Production)

```python
from packages.kernel_common.persistence import create_indexes

# Tenant & User indexes
create_indexes("tenants", [("tenant_id", 1)])
create_indexes("users", [("tenant_id", 1), ("email", 1)])
create_indexes("projects", [("tenant_id", 1), ("project_id", 1)])
create_indexes("api_tokens", [("token_value", 1), ("tenant_id", 1)])

# Version & Evidence indexes
create_indexes("goal_versions", [("tenant_id", 1), ("version_id", 1)])
create_indexes("evidence", [("tenant_id", 1), ("run_id", 1), ("timestamp", -1)])
```

### Verify Connection

```bash
# Check health endpoint
curl http://localhost:8001/health/detailed

# Expected response:
{
  "status": "ok",
  "services": {
    "persistence": {
      "status": "healthy",
      "mode": "mongodb",
      "mongodb_version": "6.0.3",
      "database": "dyocense"
    }
  }
}
```

---

## Phase 2: Keycloak Authentication

### Option A: Keycloak Cloud (Red Hat SSO)

1. **Create Account**
   - Sign up at https://www.keycloak.org/getting-started/getting-started-cloud

2. **Create Realm**
   - Navigate to Admin Console
   - Create new realm: `dyocense`
   - Note the realm URL

3. **Create Client**
   - Clients → Create Client
   - Client ID: `dyocense-api`
   - Client authentication: ON
   - Valid redirect URIs: `http://localhost:8001/*`
   - Note the client secret

### Option B: Self-Hosted Keycloak

```bash
# Docker
docker run -d \
  --name keycloak \
  -p 8080:8080 \
  -e KEYCLOAK_ADMIN=admin \
  -e KEYCLOAK_ADMIN_PASSWORD=admin \
  quay.io/keycloak/keycloak:latest \
  start-dev

# Access at: http://localhost:8080
# Create realm: dyocense
# Create client: dyocense-api
```

### Environment Variables

```bash
KEYCLOAK_SERVER_URL=http://localhost:8080
KEYCLOAK_REALM=dyocense
KEYCLOAK_CLIENT_ID=dyocense-api
KEYCLOAK_CLIENT_SECRET=<your-client-secret>

# Admin credentials (for user management)
KEYCLOAK_ADMIN_USERNAME=admin
KEYCLOAK_ADMIN_PASSWORD=admin
```

### Install Dependencies

```bash
pip install PyJWT cryptography requests
```

### Verify Authentication

```bash
# 1. Get token from Keycloak
TOKEN=$(curl -X POST "http://localhost:8080/realms/dyocense/protocol/openid-connect/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "client_id=dyocense-api" \
  -d "client_secret=<secret>" \
  -d "grant_type=client_credentials" | jq -r '.access_token')

# 2. Call API with token
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8001/v1/tenants/me
```

### Disable Keycloak (Fallback to Demo Tokens)

```bash
USE_KEYCLOAK=false

# OR force in-memory mode
FORCE_INMEMORY_MODE=true
```

---

## Phase 3: LLM Services

### Option A: Azure OpenAI (Recommended for Enterprise)

1. **Create Azure OpenAI Resource**
   ```
   - Portal: https://portal.azure.com
   - Create "Azure OpenAI" resource
   - Deploy model: gpt-4 or gpt-4-turbo
   - Note: endpoint, API key, deployment name
   ```

2. **Environment Variables**
   ```bash
   LLM_PROVIDER=azure
   AZURE_OPENAI_ENDPOINT=https://<resource-name>.openai.azure.com
   AZURE_OPENAI_API_KEY=<your-api-key>
   AZURE_OPENAI_DEPLOYMENT=gpt-4
   AZURE_OPENAI_API_VERSION=2024-02-15-preview
   
   # Tuning
   LLM_TEMPERATURE=0.7
   LLM_MAX_TOKENS=4000
   LLM_TIMEOUT=30
   ```

3. **Install Dependencies**
   ```bash
   pip install azure-ai-inference
   # OR
   pip install openai
   ```

### Option B: OpenAI API

```bash
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4
OPENAI_ORGANIZATION=org-...  # Optional
```

### Verify LLM Integration

```bash
# Test compiler service
curl -X POST http://localhost:8001/v1/compiler/compile \
  -H "Authorization: Bearer demo-tenant" \
  -H "Content-Type: application/json" \
  -d '{
    "goal": "Optimize inventory levels",
    "archetype_id": "inventory_planning"
  }'

# Check for validation_notes - should NOT contain "fallback compiler stub"
```

---

## Phase 4: Graph & Vector Stores

### Neo4j (Evidence Graph)

#### Option A: Neo4j AuraDB (Cloud)
```bash
NEO4J_URI=neo4j+s://<instance-id>.databases.neo4j.io
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=<your-password>
NEO4J_DATABASE=neo4j
```

#### Option B: Self-Hosted
```bash
docker run -d \
  --name neo4j \
  -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/password \
  neo4j:5.13

NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=password
```

### Qdrant (Vector Search)

#### Option A: Qdrant Cloud
```bash
QDRANT_URL=https://<cluster-id>.aws.cloud.qdrant.io
QDRANT_API_KEY=<your-api-key>
QDRANT_COLLECTION=dyocense_knowledge
```

#### Option B: Self-Hosted
```bash
docker run -d \
  --name qdrant \
  -p 6333:6333 \
  qdrant/qdrant

QDRANT_URL=http://localhost:6333
QDRANT_COLLECTION=dyocense_knowledge
```

### Install Dependencies

```bash
pip install neo4j qdrant-client
```

---

## Health Checks & Monitoring

### Health Endpoint

```bash
# Quick health check
curl http://localhost:8001/healthz
# → {"status": "ok"}

# Detailed health with dependency status
curl http://localhost:8001/health/detailed
```

**Response Structure:**
```json
{
  "status": "ok",  // ok | degraded | unhealthy
  "version": "0.6.0",
  "services": {
    "persistence": {
      "status": "healthy",
      "mode": "mongodb",
      "mongodb_version": "6.0.3",
      "database": "dyocense"
    },
    "authentication": {
      "status": "healthy",
      "server_url": "http://localhost:8080",
      "realm": "dyocense"
    }
  }
}
```

### Status Interpretation

- **healthy**: Service connected and operational
- **degraded**: Using fallback/stub (development mode)
- **unhealthy**: Connection failed, operations may fail

### Monitoring Recommendations

1. **Application Monitoring**
   ```python
   # Add to your monitoring system
   import requests
   
   health = requests.get("http://localhost:8001/health/detailed").json()
   
   # Alert if status != "ok"
   if health["status"] != "ok":
       send_alert(f"Dyocense unhealthy: {health}")
   
   # Alert if any service in degraded mode (production)
   for service, status in health["services"].items():
       if status["mode"] in ["fallback", "in-memory"]:
           send_alert(f"{service} using fallback mode")
   ```

2. **Metrics to Track**
   - Fallback activation rate (should be 0% in production)
   - Demo token usage (should be 0 in production)
   - Database connection pool usage
   - LLM request latency and errors
   - API response times

---

## Migration from Development

### Export In-Memory Data

Before deploying MongoDB, export existing in-memory data:

```python
# Run this before shutting down development server
import json
from pathlib import Path
from packages.kernel_common.persistence import _inmem_collections

def export_inmem_data(output_dir: str = "./data_export"):
    Path(output_dir).mkdir(exist_ok=True)
    
    for name, coll in _inmem_collections.items():
        data = list(coll._documents)
        if data:
            with open(f"{output_dir}/{name}.json", "w") as f:
                json.dump(data, f, indent=2, default=str)
            print(f"Exported {len(data)} documents from {name}")

export_inmem_data()
```

### Import to MongoDB

```python
import json
from pathlib import Path
from pymongo import MongoClient

def import_to_mongodb(input_dir: str = "./data_export"):
    client = MongoClient(os.getenv("MONGO_URI"))
    db = client[os.getenv("MONGO_DB_NAME", "dyocense")]
    
    for file_path in Path(input_dir).glob("*.json"):
        coll_name = file_path.stem
        with open(file_path) as f:
            documents = json.load(f)
        
        if documents:
            # Clear existing data
            db[coll_name].delete_many({})
            # Insert migrated data
            db[coll_name].insert_many(documents)
            print(f"Imported {len(documents)} documents to {coll_name}")

import_to_mongodb()
```

### Gradual Migration Strategy

1. **Phase 1: MongoDB Only**
   ```bash
   USE_MONGODB=true
   USE_KEYCLOAK=false  # Keep demo tokens
   USE_NEO4J=false
   USE_QDRANT=false
   USE_LLM=false
   ```

2. **Phase 2: Add Authentication**
   ```bash
   USE_KEYCLOAK=true
   # Migrate users to Keycloak, update tokens
   ```

3. **Phase 3: Add Intelligence**
   ```bash
   USE_LLM=true
   USE_QDRANT=true
   USE_NEO4J=true
   ```

---

## Troubleshooting

### MongoDB Connection Issues

```bash
# Test connection manually
mongosh "mongodb://user:pass@host:27017/dyocense"

# Check logs
tail -f logs/kernel.log | grep -i mongo

# Common issues:
# 1. Wrong credentials → Check MONGO_USERNAME/PASSWORD
# 2. IP not whitelisted → Add IP to MongoDB Atlas
# 3. Firewall blocking → Check port 27017 accessibility
```

### Keycloak Authentication Failures

```bash
# Verify Keycloak is accessible
curl http://localhost:8080/realms/dyocense

# Get realm public key
curl http://localhost:8080/realms/dyocense

# Test token generation
curl -X POST "http://localhost:8080/realms/dyocense/protocol/openid-connect/token" \
  -d "client_id=dyocense-api" \
  -d "client_secret=<secret>" \
  -d "grant_type=client_credentials"
```

### Fallback Mode Detection

If services are unexpectedly using fallbacks:

```bash
# Check health endpoint
curl http://localhost:8001/health/detailed | jq '.services'

# Look for:
# - "mode": "in-memory" → MongoDB not connected
# - "mode": "fallback" → Keycloak not connected
# - "status": "degraded" → Using stubs

# Check feature flags
env | grep USE_
env | grep FORCE_INMEMORY
```

### Performance Issues

```bash
# MongoDB slow queries
# 1. Check indexes
db.currentOp({"secs_running": {$gt: 1}})

# 2. Enable profiling
db.setProfilingLevel(1, {slowms: 100})
db.system.profile.find().sort({ts: -1}).limit(10)

# LLM timeouts
# Increase timeout
LLM_TIMEOUT=60

# Connection pool exhausted
MONGO_MAX_POOL_SIZE=100
```

---

## Production Checklist

Before going live:

- [ ] MongoDB configured with authentication and TLS
- [ ] MongoDB indexes created for all collections
- [ ] Keycloak configured with production realm
- [ ] Demo token authentication disabled (`USE_KEYCLOAK=true`)
- [ ] `FORCE_INMEMORY_MODE=false`
- [ ] `STRICT_MODE=true` (fail on dependency issues)
- [ ] `ALLOW_ANONYMOUS=false`
- [ ] LLM API keys configured with rate limits
- [ ] Health checks returning "healthy" for all services
- [ ] Monitoring and alerting configured
- [ ] Backup strategy defined for MongoDB
- [ ] TLS/HTTPS enabled on API gateway
- [ ] Secrets managed via vault (not plain text .env)
- [ ] Log aggregation configured
- [ ] Load testing performed

---

## Support

- **Documentation**: `/docs/`
- **API Spec**: `/docs/openapi/openapi.yaml`
- **Health Check**: `GET /health/detailed`
- **Stubs Reference**: `/docs/STUBS_AND_FALLBACKS.md`
