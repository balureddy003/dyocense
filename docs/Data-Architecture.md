PostgreSQL Schema Design
1. Business Metrics (TimescaleDB Hypertable)
Purpose: Store all business KPIs as time-series data

Schema:

Partition Key: time (automatic via TimescaleDB), tenant_id (manual partitioning)
Retention Policy: 12 months rolling window (configurable per tenant tier)
Compression: Automatic after 7 days
Key Tables:

business_metrics_raw: Ingested data from connectors (append-only)
business_metrics_aggregated: Hourly/daily/monthly rollups (materialized views)
metric_definitions: Metadata (metric_type, unit, calculation_formula)
Indexes:

B-tree on (tenant_id, metric_type, time DESC)
GiST on time for range queries
2. Evidence Graph (Apache AGE or JSONB)
Purpose: Causal relationships between business events and metrics

Graph Schema:

Nodes: MetricNode, EventNode, GoalNode, ExternalFactorNode
Edges: causes, correlates, inhibits, supports, influenced_by
Alternative JSONB Schema (if AGE complexity too high):
CREATE TABLE evidence_edges (
  id UUID PRIMARY KEY,
  tenant_id UUID NOT NULL,
  source_node JSONB NOT NULL,  -- {type: "metric", id: "revenue", value: 50000}
  target_node JSONB NOT NULL,
  edge_type TEXT NOT NULL,  -- "causes", "correlates"
  confidence DECIMAL(3,2),  -- 0.0 to 1.0
  evidence JSONB,  -- {method: "granger_causality", p_value: 0.03}
  created_at TIMESTAMP DEFAULT NOW()
);
CREATE INDEX idx_evidence_tenant ON evidence_edges(tenant_id);
CREATE INDEX idx_evidence_graph ON evidence_edges USING GIN (source_node, target_node);
3. SMART Goals
Purpose: Full lifecycle tracking from creation to completion

Schema:

CREATE TABLE smart_goals (
  id UUID PRIMARY KEY,
  tenant_id UUID NOT NULL,
  user_id UUID NOT NULL,
  status TEXT NOT NULL,  -- draft, active, on_track, at_risk, completed, abandoned
  
  -- SMART components (JSONB for flexibility)
  specific JSONB NOT NULL,  -- {description, focus_area, owner}
  measurable JSONB NOT NULL,  -- {primary_metric_id, target_value, current_value, unit}
  achievable JSONB NOT NULL,  -- {feasibility_score, reasoning, resources_required}
  relevant JSONB NOT NULL,  -- {aligned_metrics[], business_impact, evidence_ids[]}
  time_bound JSONB NOT NULL,  -- {start_date, target_date, milestones[]}
  
  -- Execution
  action_plan JSONB DEFAULT '[]',  -- [{task, assigned_to, due_date, status}]
  workflow_id TEXT,  -- Temporal workflow ID for orchestration
  
  -- AI coaching
  coaching_session_ids UUID[] DEFAULT '{}',
  ai_recommendations JSONB DEFAULT '[]',
  
  -- Progress tracking
  check_ins JSONB DEFAULT '[]',  -- [{timestamp, progress_pct, notes, ai_insights}]
  
  -- Evaluation
  outcome_metrics JSONB,  -- {target_achieved, final_value, completion_rate}
  
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

-- Row-Level Security for multi-tenancy
ALTER TABLE smart_goals ENABLE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation ON smart_goals
  USING (tenant_id = current_setting('app.current_tenant_id')::UUID);

-- Indexes
CREATE INDEX idx_goals_tenant_status ON smart_goals(tenant_id, status);
CREATE INDEX idx_goals_target_date ON smart_goals((time_bound->>'target_date'));
CREATE INDEX idx_goals_metric ON smart_goals USING GIN (measurable);
4. Coaching Sessions (with pgvector)
Purpose: Conversation history with semantic search

Schema:

  id UUID PRIMARY KEY,
CREATE TABLE coaching_sessions (
  id UUID PRIMARY KEY,
  tenant_id UUID NOT NULL,
  user_id UUID NOT NULL,
  session_type TEXT NOT NULL,  -- goal_discovery, progress_review, problem_solving
  
  -- Conversation
  messages JSONB DEFAULT '[]',  -- [{role, content, timestamp, metadata}]
  
  -- Semantic search
  session_summary TEXT,
  session_embedding vector(1536),  -- pgvector for OpenAI embeddings
  
  -- Context retrieval
  retrieved_context JSONB DEFAULT '[]',  -- [{type, item_id, relevance_score}]
  
  -- Outcomes
  generated_goal_ids UUID[] DEFAULT '{}',
  key_insights TEXT[],
  
  -- Quality metrics
  user_satisfaction JSONB,  -- {helpfulness, clarity, actionability, feedback}
  
  started_at TIMESTAMP DEFAULT NOW(),
  ended_at TIMESTAMP
);

-- Vector similarity search index
CREATE INDEX idx_session_embedding ON coaching_sessions 
  USING ivfflat (session_embedding vector_cosine_ops);

-- Row-Level Security
ALTER TABLE coaching_sessions ENABLE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation ON coaching_sessions
  USING (tenant_id = current_setting('app.current_tenant_id')::UUID);
5. External Benchmarks
Purpose: Industry standards, competitor data, economic indicators

Schema:
CREATE TABLE data_sources (
  id UUID PRIMARY KEY,
  tenant_id UUID NOT NULL,
  source_type TEXT NOT NULL,  -- "erpnext", "salesforce", "quickbooks"
  
  -- Configuration (encrypted at rest)
  config JSONB NOT NULL,  -- {api_url, auth_type, credentials_ref}
  field_mappings JSONB,  -- {source_field: target_metric_type}
  
  -- Sync status
  sync_status TEXT DEFAULT 'pending',  -- pending, active, error, paused
  last_sync_at TIMESTAMP,
  last_sync_status JSONB,  -- {success, records_synced, errors[]}
  next_sync_at TIMESTAMP,
  
  -- Health monitoring
  health_check_status TEXT,
  error_count INT DEFAULT 0,
  
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

ALTER TABLE data_sources ENABLE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation ON data_sources
  USING (tenant_id = current_setting('app.current_tenant_id')::UUID);

  6. Data Sources (Connector Management)
Purpose: Track connector health and sync status

Schema:
CREATE TABLE data_sources (
  id UUID PRIMARY KEY,
  tenant_id UUID NOT NULL,
  source_type TEXT NOT NULL,  -- "erpnext", "salesforce", "quickbooks"
  
  -- Configuration (encrypted at rest)
  config JSONB NOT NULL,  -- {api_url, auth_type, credentials_ref}
  field_mappings JSONB,  -- {source_field: target_metric_type}
  
  -- Sync status
  sync_status TEXT DEFAULT 'pending',  -- pending, active, error, paused
  last_sync_at TIMESTAMP,
  last_sync_status JSONB,  -- {success, records_synced, errors[]}
  next_sync_at TIMESTAMP,
  
  -- Health monitoring
  health_check_status TEXT,
  error_count INT DEFAULT 0,
  
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

ALTER TABLE data_sources ENABLE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation ON data_sources
  USING (tenant_id = current_setting('app.current_tenant_id')::UUID);

  Data Partitioning Strategy
TimescaleDB Automatic Partitioning: Hypertables partitioned by time (weekly chunks)
Manual Partitioning by Tenant: Large tables use declarative partitioning
Archival Strategy: Move data >12 months to cold storage (PostgreSQL foreign tables to S3/MinIO)
Backup & Disaster Recovery
Continuous WAL Archiving: pgBackRest or Barman
Point-in-Time Recovery (PITR): Restore to any second within retention window
Cross-Region Replication: Logical replication to standby PostgreSQL instance
Snapshot Strategy: Daily full backups, hourly incremental