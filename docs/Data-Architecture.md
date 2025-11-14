# 🗄️ Data Architecture

**Version:** 4.0 (PostgreSQL-Only)  
**Last Updated:** November 14, 2025  
**Status:** Active Development

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [PostgreSQL Extensions](#postgresql-extensions)
3. [Schema Design](#schema-design)
4. [Row-Level Security (RLS)](#row-level-security-rls)
5. [Indexing Strategy](#indexing-strategy)
6. [Data Partitioning](#data-partitioning)
7. [Backup & Recovery](#backup--recovery)

---

## 🎯 Overview

### **Single Database Philosophy**

> **"PostgreSQL is the only database you need"**

**v4.0 eliminates all specialized databases:**

| Workload | v3.0 (Specialized DB) | v4.0 (PostgreSQL Extension) | Savings |
|----------|----------------------|----------------------------|---------|
| **Time-Series** | InfluxDB ($200/mo) | TimescaleDB (free) | $200/mo |
| **Vector Search** | Pinecone ($200/mo) | pgvector (free) | $200/mo |
| **Graph Queries** | Neo4j ($500/mo) | Apache AGE (free) | $500/mo |
| **Full-Text Search** | Elasticsearch ($300/mo) | PostgreSQL tsvector (free) | $300/mo |
| **Total Savings** | **$1200/month** | **$0** | **$1200/mo** |

---

### **Key Design Decisions**

1. **PostgreSQL 16+ Only** → All data (relational, time-series, vector, graph) in one DB
2. **Row-Level Security (RLS)** → Tenant isolation enforced at database layer
3. **JSONB for Flexibility** → Semi-structured data without schema migrations
4. **TimescaleDB for Metrics** → Automatic partitioning, compression, continuous aggregates
5. **pgvector for RAG** → Semantic search for coaching sessions
6. **Apache AGE for Causality** → Store causal graphs (optional, can use JSONB)

---

## 🔌 PostgreSQL Extensions

### **1. TimescaleDB (Time-Series Data)**

**Purpose:** Store business metrics efficiently

**Installation:**

```sql
CREATE EXTENSION IF NOT EXISTS timescaledb;
```

**Features:**

- **Hypertables:** Automatic time-based partitioning (weekly chunks)
- **Compression:** 90% storage reduction for historical data
- **Continuous Aggregates:** Pre-computed hourly/daily/monthly rollups
- **Retention Policies:** Automatically drop old data (e.g., >12 months)

**Example:**

```sql
CREATE TABLE business_metrics (
  time TIMESTAMPTZ NOT NULL,
  tenant_id UUID NOT NULL,
  metric_name TEXT NOT NULL,
  value NUMERIC NOT NULL,
  unit TEXT,
  metadata JSONB
);

-- Convert to hypertable
SELECT create_hypertable('business_metrics', 'time');

-- Enable compression (after 7 days)
ALTER TABLE business_metrics SET (
  timescaledb.compress,
  timescaledb.compress_segmentby = 'tenant_id,metric_name'
);

SELECT add_compression_policy('business_metrics', INTERVAL '7 days');
```

---

### **2. pgvector (Vector Search for RAG)**

**Purpose:** Semantic search over coaching sessions, documents

**Installation:**

```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

**Features:**

- **384-dim vectors** (Sentence Transformers: all-MiniLM-L6-v2)
- **Similarity search** (cosine, L2, inner product)
- **IVFFlat index** (approximate nearest neighbors, 10x faster)

**Example:**

```sql
CREATE TABLE coaching_sessions (
  id UUID PRIMARY KEY,
  tenant_id UUID NOT NULL,
  user_query TEXT NOT NULL,
  query_embedding vector(384),
  coach_response TEXT NOT NULL,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create IVFFlat index (lists=100 for 10K-100K rows)
CREATE INDEX idx_embedding ON coaching_sessions 
USING ivfflat (query_embedding vector_cosine_ops)
WITH (lists = 100);

-- Query: Find 5 most similar sessions
SELECT id, user_query, 
       1 - (query_embedding <=> '[0.1, 0.2, ...]'::vector) AS similarity
FROM coaching_sessions
WHERE tenant_id = 'abc-123'
ORDER BY query_embedding <=> '[0.1, 0.2, ...]'::vector
LIMIT 5;
```

---

### **3. Apache AGE (Graph Queries)**

**Purpose:** Store causal graphs (evidence relationships)

**Installation:**

```sql
LOAD 'age';
SET search_path = ag_catalog, "$user", public;
```

**Features:**

- **Cypher queries** (same as Neo4j)
- **Property graphs** (nodes + edges with attributes)
- **Path queries** (find causal chains)

**Example:**

```sql
-- Create graph
SELECT create_graph('evidence_graph');

-- Add nodes
SELECT * FROM cypher('evidence_graph', $$
  CREATE (m1:Metric {name: 'revenue', value: 50000})
  CREATE (m2:Metric {name: 'marketing_spend', value: 5000})
  CREATE (m1)-[:CAUSED_BY {confidence: 0.85, method: 'granger'}]->(m2)
$$) as (result agtype);

-- Query: Find what causes revenue changes
SELECT * FROM cypher('evidence_graph', $$
  MATCH (m1:Metric {name: 'revenue'})<-[:CAUSED_BY]-(m2)
  RETURN m2.name, m2.value
$$) as (cause_name agtype, cause_value agtype);
```

**Alternative (JSONB):** If AGE complexity is too high, store graph as JSONB:

```sql
CREATE TABLE evidence_graph (
  id UUID PRIMARY KEY,
  tenant_id UUID NOT NULL,
  graph_data JSONB NOT NULL,  -- {nodes: [...], edges: [...]}
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Example graph_data:
{
  "nodes": [
    {"id": "revenue", "type": "metric", "value": 50000},
    {"id": "marketing_spend", "type": "metric", "value": 5000}
  ],
  "edges": [
    {"from": "marketing_spend", "to": "revenue", "type": "causes", "confidence": 0.85}
  ]
}
```

---

### **4. pg_cron (Scheduled Jobs)**

**Purpose:** Automated data refresh, aggregations

**Installation:**

```sql
CREATE EXTENSION IF NOT EXISTS pg_cron;
```

**Features:**

- **Cron syntax** (same as Linux cron)
- **Runs inside PostgreSQL** (no external scheduler needed)
- **SQL jobs** (call functions, refresh materialized views)

**Example:**

```sql
-- Refresh external benchmarks daily at 2 AM
SELECT cron.schedule(
  'refresh-benchmarks',
  '0 2 * * *',  -- Every day at 2 AM
  $$CALL refresh_external_benchmarks();$$
);

-- Recompute hourly aggregates every hour
SELECT cron.schedule(
  'hourly-rollups',
  '0 * * * *',  -- Every hour
  $$REFRESH MATERIALIZED VIEW CONCURRENTLY business_metrics_hourly;$$
);
```

---

## 📊 Schema Design

### **Core Tables**

#### **1. Tenants (Companies)**

```sql
CREATE TABLE tenants (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name TEXT NOT NULL,
  industry TEXT, -- 'restaurant', 'retail', 'healthcare'
  subscription_tier TEXT DEFAULT 'starter', -- 'starter', 'pro', 'enterprise'
  is_active BOOLEAN DEFAULT true,
  created_at TIMESTAMPTZ DEFAULT NOW()
);
```

---

#### **2. Users (SMB Employees)**

```sql
CREATE TABLE users (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,
  email TEXT UNIQUE NOT NULL,
  password_hash TEXT NOT NULL,
  role TEXT DEFAULT 'member', -- 'admin', 'manager', 'member'
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_users_tenant ON users(tenant_id);

-- Row-Level Security
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation ON users
USING (tenant_id = current_setting('app.current_tenant')::uuid);
```

---

#### **3. Business Metrics (TimescaleDB Hypertable)**

```sql
CREATE TABLE business_metrics (
  time TIMESTAMPTZ NOT NULL,
  tenant_id UUID NOT NULL,
  metric_name TEXT NOT NULL, -- 'revenue', 'sales_count', 'inventory_level'
  value NUMERIC NOT NULL,
  unit TEXT, -- 'USD', 'count', 'units'
  metadata JSONB, -- Flexible additional context
  PRIMARY KEY (time, tenant_id, metric_name)
);

-- Convert to TimescaleDB hypertable
SELECT create_hypertable('business_metrics', 'time');

-- Enable compression (after 7 days)
ALTER TABLE business_metrics SET (
  timescaledb.compress,
  timescaledb.compress_segmentby = 'tenant_id,metric_name'
);
SELECT add_compression_policy('business_metrics', INTERVAL '7 days');

-- Retention policy (drop data >24 months)
SELECT add_retention_policy('business_metrics', INTERVAL '24 months');

-- Row-Level Security
ALTER TABLE business_metrics ENABLE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation ON business_metrics
USING (tenant_id = current_setting('app.current_tenant')::uuid);
```

---

#### **4. SMART Goals**

```sql
CREATE TABLE smart_goals (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,
  user_id UUID REFERENCES users(id) ON DELETE CASCADE,
  
  -- Basic info
  title TEXT NOT NULL,
  description TEXT,
  status TEXT DEFAULT 'in_progress', -- 'created', 'in_progress', 'completed', 'archived'
  
  -- SMART components (JSONB for flexibility)
  specific JSONB NOT NULL,  -- {focus_area, owner, description}
  measurable JSONB NOT NULL,  -- {primary_metric, target_value, current_value, unit}
  achievable JSONB NOT NULL,  -- {feasibility_score, resources_required}
  relevant JSONB NOT NULL,  -- {aligned_business_goals[], impact_areas[]}
  time_bound JSONB NOT NULL,  -- {start_date, target_date, milestones[]}
  
  -- Progress tracking
  check_ins JSONB DEFAULT '[]', -- [{timestamp, progress_pct, notes}]
  
  -- Evaluation
  outcome JSONB, -- {target_achieved, final_value, completion_rate, learnings}
  
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_goals_tenant_status ON smart_goals(tenant_id, status);
CREATE INDEX idx_goals_target_date ON smart_goals((time_bound->>'target_date'));

-- Row-Level Security
ALTER TABLE smart_goals ENABLE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation ON smart_goals
USING (tenant_id = current_setting('app.current_tenant')::uuid);
```

---

#### **5. Coaching Sessions (with Embeddings)**

```sql
CREATE EXTENSION vector;

CREATE TABLE coaching_sessions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,
  user_id UUID REFERENCES users(id) ON DELETE CASCADE,
  
  -- Conversation
  user_query TEXT NOT NULL,
  query_embedding vector(384), -- Sentence Transformers
  coach_response TEXT NOT NULL,
  
  -- LLM metadata
  llm_provider TEXT, -- 'local_llama3' or 'openai_gpt4o'
  response_time_ms INT,
  cost_usd NUMERIC(10, 6),
  
  -- Context
  retrieved_context JSONB DEFAULT '[]', -- RAG sources
  
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Vector similarity index
CREATE INDEX idx_embedding ON coaching_sessions 
USING ivfflat (query_embedding vector_cosine_ops)
WITH (lists = 100);

CREATE INDEX idx_sessions_tenant ON coaching_sessions(tenant_id);

-- Row-Level Security
ALTER TABLE coaching_sessions ENABLE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation ON coaching_sessions
USING (tenant_id = current_setting('app.current_tenant')::uuid);
```

---

#### **6. Evidence Graph (Causal Relationships)**

**Option A: JSONB (Simpler)**

```sql
CREATE TABLE evidence_graph (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,
  graph_data JSONB NOT NULL, -- {nodes: [...], edges: [...]}
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_graph_tenant ON evidence_graph(tenant_id);

-- Row-Level Security
ALTER TABLE evidence_graph ENABLE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation ON evidence_graph
USING (tenant_id = current_setting('app.current_tenant')::uuid);
```

**Option B: Apache AGE (More Powerful)**

```sql
-- Create graph per tenant (dynamic)
SELECT create_graph('tenant_abc123_evidence');

-- Nodes and edges created via Cypher queries (see AGE section above)
```

---

#### **7. Data Sources (Connectors)**

```sql
CREATE TABLE data_sources (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,
  
  source_type TEXT NOT NULL, -- 'quickbooks', 'shopify', 'stripe'
  config JSONB NOT NULL, -- {api_url, credentials_encrypted, field_mappings}
  
  -- Sync status
  sync_status TEXT DEFAULT 'pending', -- 'pending', 'active', 'error', 'paused'
  last_sync_at TIMESTAMPTZ,
  next_sync_at TIMESTAMPTZ,
  error_count INT DEFAULT 0,
  
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_sources_tenant ON data_sources(tenant_id);

-- Row-Level Security
ALTER TABLE data_sources ENABLE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation ON data_sources
USING (tenant_id = current_setting('app.current_tenant')::uuid);
```

---

#### **8. External Benchmarks (Industry Data)**

```sql
CREATE TABLE external_benchmarks (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  source TEXT NOT NULL, -- 'fred', 'ibisworld', 'census'
  industry TEXT, -- 'restaurant', 'retail', NULL (for economy-wide)
  metric_name TEXT NOT NULL,
  value NUMERIC NOT NULL,
  time_period TIMESTAMPTZ NOT NULL,
  metadata JSONB, -- {units, methodology, source_url}
  
  created_at TIMESTAMPTZ DEFAULT NOW(),
  
  UNIQUE(source, metric_name, time_period)
);

CREATE INDEX idx_benchmarks_industry ON external_benchmarks(industry, metric_name);
```

---

## 🔒 Row-Level Security (RLS)

### **How It Works**

Every request sets a session variable:

```python
# FastAPI middleware
@app.middleware("http")
async def set_tenant_context(request: Request, call_next):
    tenant_id = get_tenant_from_jwt(request.headers["Authorization"])
    
    async with db.begin():
        await db.execute(f"SET app.current_tenant = '{tenant_id}'")
        response = await call_next(request)
    
    return response
```

PostgreSQL RLS policy automatically filters queries:

```sql
-- User queries: SELECT * FROM business_metrics;
-- PostgreSQL executes: SELECT * FROM business_metrics WHERE tenant_id = 'abc-123';
```

**Benefits:**

- ✅ **Zero application-level bugs** (database enforces isolation)
- ✅ **Audit-friendly** (policy violations logged)
- ✅ **Performance** (PostgreSQL optimizes with tenant_id in WHERE clause)

---

## 📈 Indexing Strategy

### **Primary Indexes**

```sql
-- Tenant-scoped queries (most common)
CREATE INDEX idx_metrics_tenant_time ON business_metrics(tenant_id, time DESC);
CREATE INDEX idx_goals_tenant_status ON smart_goals(tenant_id, status);
CREATE INDEX idx_sessions_tenant_created ON coaching_sessions(tenant_id, created_at DESC);

-- JSONB queries (GIN index)
CREATE INDEX idx_goals_measurable ON smart_goals USING GIN (measurable);
CREATE INDEX idx_graph_data ON evidence_graph USING GIN (graph_data);

-- Vector similarity (IVFFlat)
CREATE INDEX idx_embedding ON coaching_sessions 
USING ivfflat (query_embedding vector_cosine_ops) WITH (lists = 100);

-- Full-text search (GIN on tsvector)
CREATE INDEX idx_goals_fulltext ON smart_goals 
USING GIN (to_tsvector('english', title || ' ' || description));
```

---

## 🗂️ Data Partitioning

### **TimescaleDB Automatic Partitioning**

Hypertables automatically partitioned by time (weekly chunks):

```sql
SELECT create_hypertable('business_metrics', 'time', chunk_time_interval => INTERVAL '7 days');
```

**Benefits:**

- ✅ **Query optimization** (only scan relevant chunks)
- ✅ **Compression** (old chunks compressed automatically)
- ✅ **Retention** (drop old chunks without scanning entire table)

---

### **Manual Partitioning by Tenant (Optional)**

For very large tenants (>10M rows), partition by tenant:

```sql
CREATE TABLE coaching_sessions (
  ...
) PARTITION BY LIST (tenant_id);

CREATE TABLE coaching_sessions_tenant_abc PARTITION OF coaching_sessions
FOR VALUES IN ('abc-123-uuid');
```

---

## 💾 Backup & Recovery

### **Continuous WAL Archiving**

```bash
# Install pgBackRest
sudo apt-get install pgbackrest

# Configure WAL archiving
# postgresql.conf:
archive_mode = on
archive_command = 'pgbackrest --stanza=dyocense archive-push %p'

# Take daily full backup
pgbackrest --stanza=dyocense --type=full backup

# Take hourly incremental backups
pgbackrest --stanza=dyocense --type=incr backup
```

---

### **Point-in-Time Recovery (PITR)**

```bash
# Restore to specific timestamp
pgbackrest --stanza=dyocense --type=time --target="2025-11-14 10:30:00" restore
```

---

### **Cross-Region Replication**

```sql
-- On primary (write master)
CREATE PUBLICATION dyocense_pub FOR ALL TABLES;

-- On standby (read replica)
CREATE SUBSCRIPTION dyocense_sub
CONNECTION 'host=primary.db.com dbname=dyocense'
PUBLICATION dyocense_pub;
```

**Use Cases:**

- ✅ **Disaster recovery** (failover to standby)
- ✅ **Read scaling** (route read queries to replicas)
- ✅ **Multi-region** (low-latency reads in each region)

---

## 🎯 Next Steps

1. **Review [Technology Stack Selection](./Technology Stack Selection.md)** for extension rationale
2. **Review [Security & Multi-Tenancy](./Security & Multi-Tenancy.md)** for RLS deep dive
3. **Start Phase 0** of [Implementation Roadmap](./Implementation-Roadmap.md)

**Ready to implement! 🚀**
