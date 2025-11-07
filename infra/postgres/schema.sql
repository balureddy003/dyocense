-- =====================================================================
-- Dyocense SMB-Optimized PostgreSQL Schema
-- =====================================================================
-- Purpose: Consolidated database for cost-efficient SMB deployments
-- Features: Multi-tenancy, JSONB for flexibility, pgvector for embeddings
-- Target: 50+ tenants, <100GB data, <$150/month infrastructure cost
-- =====================================================================

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
CREATE EXTENSION IF NOT EXISTS "vector";

-- =====================================================================
-- Schema Organization
-- =====================================================================
CREATE SCHEMA IF NOT EXISTS tenants;
CREATE SCHEMA IF NOT EXISTS runs;
CREATE SCHEMA IF NOT EXISTS connectors;
CREATE SCHEMA IF NOT EXISTS evidence;
CREATE SCHEMA IF NOT EXISTS knowledge;
CREATE SCHEMA IF NOT EXISTS system;

-- =====================================================================
-- TENANTS SCHEMA
-- =====================================================================

CREATE TABLE tenants.tenants (
  tenant_id TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
  name TEXT NOT NULL,
  owner_email TEXT NOT NULL,
  plan_tier TEXT NOT NULL DEFAULT 'smb_starter',
  api_token TEXT NOT NULL UNIQUE DEFAULT encode(gen_random_bytes(32), 'base64'),
  status TEXT NOT NULL DEFAULT 'active',
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  metadata JSONB DEFAULT '{}',
  
  -- Resource limits based on tier
  limits JSONB DEFAULT jsonb_build_object(
    'max_users', 10,
    'max_projects', 50,
    'max_runs_per_month', 1000,
    'max_connectors', 10,
    'max_storage_gb', 10
  ),
  
  -- Usage tracking
  usage JSONB DEFAULT jsonb_build_object(
    'users_count', 0,
    'projects_count', 0,
    'runs_this_month', 0,
    'connectors_count', 0,
    'storage_used_gb', 0
  ),
  
  CONSTRAINT valid_plan_tier CHECK (plan_tier IN ('smb_starter', 'smb_growth', 'enterprise'))
);

CREATE INDEX idx_tenants_status ON tenants.tenants(status);
CREATE INDEX idx_tenants_plan_tier ON tenants.tenants(plan_tier);
CREATE INDEX idx_tenants_owner_email ON tenants.tenants(owner_email);

CREATE TABLE tenants.users (
  user_id TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
  tenant_id TEXT NOT NULL REFERENCES tenants.tenants(tenant_id) ON DELETE CASCADE,
  email TEXT NOT NULL,
  full_name TEXT,
  password_hash TEXT,
  roles TEXT[] NOT NULL DEFAULT ARRAY['member'],
  status TEXT NOT NULL DEFAULT 'active',
  last_login TIMESTAMPTZ,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  metadata JSONB DEFAULT '{}',
  
  CONSTRAINT unique_tenant_email UNIQUE(tenant_id, email),
  CONSTRAINT valid_status CHECK (status IN ('active', 'suspended', 'deleted'))
);

CREATE INDEX idx_users_tenant ON tenants.users(tenant_id);
CREATE INDEX idx_users_email ON tenants.users(email);
CREATE INDEX idx_users_status ON tenants.users(tenant_id, status);

CREATE TABLE tenants.projects (
  project_id TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
  tenant_id TEXT NOT NULL REFERENCES tenants.tenants(tenant_id) ON DELETE CASCADE,
  name TEXT NOT NULL,
  description TEXT,
  archetype TEXT,
  owner_id TEXT REFERENCES tenants.users(user_id),
  status TEXT NOT NULL DEFAULT 'active',
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  metadata JSONB DEFAULT '{}',
  
  CONSTRAINT unique_tenant_project_name UNIQUE(tenant_id, name)
);

CREATE INDEX idx_projects_tenant ON tenants.projects(tenant_id);
CREATE INDEX idx_projects_owner ON tenants.projects(owner_id);

-- =====================================================================
-- RUNS SCHEMA
-- =====================================================================

CREATE TABLE runs.runs (
  run_id TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
  tenant_id TEXT NOT NULL REFERENCES tenants.tenants(tenant_id) ON DELETE CASCADE,
  project_id TEXT REFERENCES tenants.projects(project_id) ON DELETE SET NULL,
  user_id TEXT REFERENCES tenants.users(user_id) ON DELETE SET NULL,
  status TEXT NOT NULL DEFAULT 'pending',
  
  -- Core payload and results
  ops_payload JSONB NOT NULL,
  solution_pack JSONB,
  
  -- Execution metadata
  started_at TIMESTAMPTZ,
  completed_at TIMESTAMPTZ,
  duration_seconds NUMERIC,
  
  -- Error tracking
  error_message TEXT,
  error_details JSONB,
  
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  metadata JSONB DEFAULT '{}',
  
  CONSTRAINT valid_status CHECK (status IN ('pending', 'running', 'completed', 'failed', 'cancelled'))
);

CREATE INDEX idx_runs_tenant ON runs.runs(tenant_id, created_at DESC);
CREATE INDEX idx_runs_project ON runs.runs(project_id, created_at DESC);
CREATE INDEX idx_runs_status ON runs.runs(status, created_at DESC);
CREATE INDEX idx_runs_user ON runs.runs(user_id);

-- GIN index for JSONB queries
CREATE INDEX idx_runs_ops_payload ON runs.runs USING GIN(ops_payload);
CREATE INDEX idx_runs_solution_pack ON runs.runs USING GIN(solution_pack);

CREATE TABLE runs.run_steps (
  step_id TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
  run_id TEXT NOT NULL REFERENCES runs.runs(run_id) ON DELETE CASCADE,
  step_name TEXT NOT NULL,
  step_type TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'pending',
  started_at TIMESTAMPTZ,
  completed_at TIMESTAMPTZ,
  duration_seconds NUMERIC,
  input_data JSONB,
  output_data JSONB,
  error_message TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  
  CONSTRAINT valid_step_status CHECK (status IN ('pending', 'running', 'completed', 'failed', 'skipped'))
);

CREATE INDEX idx_run_steps_run ON runs.run_steps(run_id, created_at);

-- =====================================================================
-- CONNECTORS SCHEMA
-- =====================================================================

CREATE TABLE connectors.connectors (
  connector_id TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
  tenant_id TEXT NOT NULL REFERENCES tenants.tenants(tenant_id) ON DELETE CASCADE,
  connector_type TEXT NOT NULL,
  display_name TEXT NOT NULL,
  
  -- Encrypted credentials
  config_encrypted BYTEA,
  encryption_key_id TEXT,
  
  status TEXT NOT NULL DEFAULT 'active',
  last_sync TIMESTAMPTZ,
  sync_status TEXT,
  sync_error TEXT,
  
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  metadata JSONB DEFAULT '{}',
  
  CONSTRAINT unique_tenant_connector_name UNIQUE(tenant_id, display_name),
  CONSTRAINT valid_status CHECK (status IN ('active', 'inactive', 'error', 'deleted'))
);

CREATE INDEX idx_connectors_tenant ON connectors.connectors(tenant_id, status);
CREATE INDEX idx_connectors_type ON connectors.connectors(connector_type);

CREATE TABLE connectors.sync_history (
  sync_id TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
  connector_id TEXT NOT NULL REFERENCES connectors.connectors(connector_id) ON DELETE CASCADE,
  started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  completed_at TIMESTAMPTZ,
  status TEXT NOT NULL DEFAULT 'running',
  records_synced INTEGER DEFAULT 0,
  error_message TEXT,
  metadata JSONB DEFAULT '{}',
  
  CONSTRAINT valid_sync_status CHECK (status IN ('running', 'completed', 'failed', 'cancelled'))
);

CREATE INDEX idx_sync_history_connector ON connectors.sync_history(connector_id, started_at DESC);

-- =====================================================================
-- EVIDENCE SCHEMA (Graph-like structure in Postgres)
-- =====================================================================

CREATE TABLE evidence.evidence_nodes (
  node_id TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
  run_id TEXT NOT NULL REFERENCES runs.runs(run_id) ON DELETE CASCADE,
  tenant_id TEXT NOT NULL REFERENCES tenants.tenants(tenant_id) ON DELETE CASCADE,
  node_type TEXT NOT NULL,
  properties JSONB NOT NULL DEFAULT '{}',
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  metadata JSONB DEFAULT '{}'
);

CREATE INDEX idx_evidence_nodes_run ON evidence.evidence_nodes(run_id);
CREATE INDEX idx_evidence_nodes_tenant ON evidence.evidence_nodes(tenant_id);
CREATE INDEX idx_evidence_nodes_type ON evidence.evidence_nodes(node_type);
CREATE INDEX idx_evidence_nodes_properties ON evidence.evidence_nodes USING GIN(properties);

CREATE TABLE evidence.evidence_edges (
  edge_id TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
  run_id TEXT NOT NULL REFERENCES runs.runs(run_id) ON DELETE CASCADE,
  tenant_id TEXT NOT NULL REFERENCES tenants.tenants(tenant_id) ON DELETE CASCADE,
  from_node TEXT NOT NULL REFERENCES evidence.evidence_nodes(node_id) ON DELETE CASCADE,
  to_node TEXT NOT NULL REFERENCES evidence.evidence_nodes(node_id) ON DELETE CASCADE,
  relationship_type TEXT NOT NULL,
  properties JSONB DEFAULT '{}',
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_evidence_edges_run ON evidence.evidence_edges(run_id);
CREATE INDEX idx_evidence_edges_from ON evidence.evidence_edges(from_node);
CREATE INDEX idx_evidence_edges_to ON evidence.evidence_edges(to_node);
CREATE INDEX idx_evidence_edges_type ON evidence.evidence_edges(relationship_type);

-- =====================================================================
-- KNOWLEDGE SCHEMA (Vector embeddings for RAG)
-- =====================================================================

CREATE TABLE knowledge.documents (
  document_id TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
  tenant_id TEXT NOT NULL REFERENCES tenants.tenants(tenant_id) ON DELETE CASCADE,
  project_id TEXT REFERENCES tenants.projects(project_id) ON DELETE SET NULL,
  content TEXT NOT NULL,
  document_type TEXT NOT NULL,
  source TEXT,
  embedding vector(1536),  -- OpenAI ada-002 dimension
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  metadata JSONB DEFAULT '{}'
);

CREATE INDEX idx_documents_tenant ON knowledge.documents(tenant_id);
CREATE INDEX idx_documents_project ON knowledge.documents(project_id);
CREATE INDEX idx_documents_type ON knowledge.documents(document_type);

-- Vector similarity search index (IVFFlat for cost-efficiency)
CREATE INDEX idx_documents_embedding ON knowledge.documents 
  USING ivfflat (embedding vector_cosine_ops)
  WITH (lists = 100);

-- Full-text search
CREATE INDEX idx_documents_content_fts ON knowledge.documents USING GIN(to_tsvector('english', content));

-- =====================================================================
-- SYSTEM SCHEMA (Events, Audit, Background Jobs)
-- =====================================================================

CREATE TABLE system.event_queue (
  event_id BIGSERIAL PRIMARY KEY,
  event_type TEXT NOT NULL,
  payload JSONB NOT NULL,
  tenant_id TEXT REFERENCES tenants.tenants(tenant_id) ON DELETE SET NULL,
  status TEXT NOT NULL DEFAULT 'pending',
  priority INTEGER DEFAULT 0,
  scheduled_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  processed_at TIMESTAMPTZ,
  error_message TEXT,
  retry_count INTEGER DEFAULT 0,
  max_retries INTEGER DEFAULT 3,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  
  CONSTRAINT valid_event_status CHECK (status IN ('pending', 'processing', 'completed', 'failed', 'cancelled'))
);

CREATE INDEX idx_event_queue_status ON system.event_queue(status, priority DESC, scheduled_at);
CREATE INDEX idx_event_queue_tenant ON system.event_queue(tenant_id);

CREATE TABLE system.audit_log (
  audit_id BIGSERIAL PRIMARY KEY,
  tenant_id TEXT REFERENCES tenants.tenants(tenant_id) ON DELETE SET NULL,
  user_id TEXT REFERENCES tenants.users(user_id) ON DELETE SET NULL,
  action TEXT NOT NULL,
  resource_type TEXT NOT NULL,
  resource_id TEXT NOT NULL,
  changes JSONB,
  ip_address INET,
  user_agent TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_audit_log_tenant ON system.audit_log(tenant_id, created_at DESC);
CREATE INDEX idx_audit_log_user ON system.audit_log(user_id, created_at DESC);
CREATE INDEX idx_audit_log_resource ON system.audit_log(resource_type, resource_id);

CREATE TABLE system.background_jobs (
  job_id TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
  job_type TEXT NOT NULL,
  tenant_id TEXT REFERENCES tenants.tenants(tenant_id) ON DELETE CASCADE,
  status TEXT NOT NULL DEFAULT 'pending',
  scheduled_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  started_at TIMESTAMPTZ,
  completed_at TIMESTAMPTZ,
  payload JSONB NOT NULL,
  result JSONB,
  error_message TEXT,
  retry_count INTEGER DEFAULT 0,
  max_retries INTEGER DEFAULT 3,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  
  CONSTRAINT valid_job_status CHECK (status IN ('pending', 'running', 'completed', 'failed', 'cancelled'))
);

CREATE INDEX idx_background_jobs_status ON system.background_jobs(status, scheduled_at);
CREATE INDEX idx_background_jobs_tenant ON system.background_jobs(tenant_id);

-- =====================================================================
-- TRIGGERS & FUNCTIONS
-- =====================================================================

-- Update timestamp trigger
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply to all relevant tables
CREATE TRIGGER update_tenants_updated_at BEFORE UPDATE ON tenants.tenants
  FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON tenants.users
  FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER update_projects_updated_at BEFORE UPDATE ON tenants.projects
  FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER update_runs_updated_at BEFORE UPDATE ON runs.runs
  FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER update_connectors_updated_at BEFORE UPDATE ON connectors.connectors
  FOR EACH ROW EXECUTE FUNCTION update_updated_at();

-- Audit log trigger for sensitive operations
CREATE OR REPLACE FUNCTION log_tenant_changes()
RETURNS TRIGGER AS $$
BEGIN
  INSERT INTO system.audit_log (tenant_id, action, resource_type, resource_id, changes)
  VALUES (
    COALESCE(NEW.tenant_id, OLD.tenant_id),
    TG_OP,
    'tenant',
    COALESCE(NEW.tenant_id, OLD.tenant_id),
    jsonb_build_object('old', to_jsonb(OLD), 'new', to_jsonb(NEW))
  );
  RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER audit_tenant_changes
  AFTER INSERT OR UPDATE OR DELETE ON tenants.tenants
  FOR EACH ROW EXECUTE FUNCTION log_tenant_changes();

-- Increment usage counters
CREATE OR REPLACE FUNCTION increment_tenant_usage()
RETURNS TRIGGER AS $$
BEGIN
  IF TG_OP = 'INSERT' THEN
    IF TG_TABLE_NAME = 'users' THEN
      UPDATE tenants.tenants 
      SET usage = jsonb_set(usage, '{users_count}', (COALESCE((usage->>'users_count')::int, 0) + 1)::text::jsonb)
      WHERE tenant_id = NEW.tenant_id;
    ELSIF TG_TABLE_NAME = 'projects' THEN
      UPDATE tenants.tenants 
      SET usage = jsonb_set(usage, '{projects_count}', (COALESCE((usage->>'projects_count')::int, 0) + 1)::text::jsonb)
      WHERE tenant_id = NEW.tenant_id;
    ELSIF TG_TABLE_NAME = 'runs' THEN
      UPDATE tenants.tenants 
      SET usage = jsonb_set(usage, '{runs_this_month}', (COALESCE((usage->>'runs_this_month')::int, 0) + 1)::text::jsonb)
      WHERE tenant_id = NEW.tenant_id;
    ELSIF TG_TABLE_NAME = 'connectors' THEN
      UPDATE tenants.tenants 
      SET usage = jsonb_set(usage, '{connectors_count}', (COALESCE((usage->>'connectors_count')::int, 0) + 1)::text::jsonb)
      WHERE tenant_id = NEW.tenant_id;
    END IF;
  END IF;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER track_user_creation AFTER INSERT ON tenants.users
  FOR EACH ROW EXECUTE FUNCTION increment_tenant_usage();

CREATE TRIGGER track_project_creation AFTER INSERT ON tenants.projects
  FOR EACH ROW EXECUTE FUNCTION increment_tenant_usage();

CREATE TRIGGER track_run_creation AFTER INSERT ON runs.runs
  FOR EACH ROW EXECUTE FUNCTION increment_tenant_usage();

CREATE TRIGGER track_connector_creation AFTER INSERT ON connectors.connectors
  FOR EACH ROW EXECUTE FUNCTION increment_tenant_usage();

-- =====================================================================
-- HELPER FUNCTIONS
-- =====================================================================

-- Vector search function
CREATE OR REPLACE FUNCTION knowledge.search_similar_documents(
  p_tenant_id TEXT,
  p_query_embedding vector(1536),
  p_limit INTEGER DEFAULT 10,
  p_threshold NUMERIC DEFAULT 0.7
)
RETURNS TABLE (
  document_id TEXT,
  content TEXT,
  similarity NUMERIC,
  metadata JSONB
) AS $$
BEGIN
  RETURN QUERY
  SELECT 
    d.document_id,
    d.content,
    1 - (d.embedding <=> p_query_embedding) AS similarity,
    d.metadata
  FROM knowledge.documents d
  WHERE d.tenant_id = p_tenant_id
    AND 1 - (d.embedding <=> p_query_embedding) >= p_threshold
  ORDER BY d.embedding <=> p_query_embedding
  LIMIT p_limit;
END;
$$ LANGUAGE plpgsql;

-- Graph traversal function
CREATE OR REPLACE FUNCTION evidence.get_connected_nodes(
  p_node_id TEXT,
  p_relationship_type TEXT DEFAULT NULL,
  p_max_depth INTEGER DEFAULT 3
)
RETURNS TABLE (
  node_id TEXT,
  node_type TEXT,
  properties JSONB,
  depth INTEGER,
  path TEXT[]
) AS $$
WITH RECURSIVE node_traversal AS (
  -- Base case: starting node
  SELECT 
    n.node_id,
    n.node_type,
    n.properties,
    0 AS depth,
    ARRAY[n.node_id] AS path
  FROM evidence.evidence_nodes n
  WHERE n.node_id = p_node_id
  
  UNION ALL
  
  -- Recursive case: connected nodes
  SELECT 
    n.node_id,
    n.node_type,
    n.properties,
    nt.depth + 1,
    nt.path || n.node_id
  FROM evidence.evidence_nodes n
  INNER JOIN evidence.evidence_edges e ON e.to_node = n.node_id
  INNER JOIN node_traversal nt ON e.from_node = nt.node_id
  WHERE nt.depth < p_max_depth
    AND n.node_id != ALL(nt.path)  -- Prevent cycles
    AND (p_relationship_type IS NULL OR e.relationship_type = p_relationship_type)
)
SELECT * FROM node_traversal;
$$ LANGUAGE sql;

-- =====================================================================
-- INITIAL DATA
-- =====================================================================

-- Create system tenant for internal operations
INSERT INTO tenants.tenants (tenant_id, name, owner_email, plan_tier, status)
VALUES ('system', 'System', 'admin@dyocense.com', 'enterprise', 'active')
ON CONFLICT (tenant_id) DO NOTHING;

-- =====================================================================
-- VIEWS
-- =====================================================================

-- Tenant health dashboard view
CREATE OR REPLACE VIEW tenants.tenant_health AS
SELECT 
  t.tenant_id,
  t.name,
  t.plan_tier,
  t.status,
  (t.usage->>'users_count')::int AS users,
  (t.usage->>'projects_count')::int AS projects,
  (t.usage->>'runs_this_month')::int AS runs_this_month,
  (t.limits->>'max_runs_per_month')::int AS max_runs_per_month,
  ROUND(
    (t.usage->>'runs_this_month')::numeric / 
    NULLIF((t.limits->>'max_runs_per_month')::numeric, 0) * 100, 
    2
  ) AS usage_percentage,
  t.created_at,
  t.updated_at
FROM tenants.tenants t
WHERE t.status = 'active';

-- Recent runs view
CREATE OR REPLACE VIEW runs.recent_runs AS
SELECT 
  r.run_id,
  r.tenant_id,
  t.name AS tenant_name,
  r.project_id,
  p.name AS project_name,
  r.status,
  r.duration_seconds,
  r.created_at,
  r.completed_at
FROM runs.runs r
LEFT JOIN tenants.tenants t ON t.tenant_id = r.tenant_id
LEFT JOIN tenants.projects p ON p.project_id = r.project_id
WHERE r.created_at >= NOW() - INTERVAL '7 days'
ORDER BY r.created_at DESC;

-- =====================================================================
-- GRANTS (Production deployment should restrict further)
-- =====================================================================

-- Grant usage on schemas
GRANT USAGE ON SCHEMA tenants, runs, connectors, evidence, knowledge, system TO PUBLIC;

-- Grant access on all tables (adjust for production)
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA tenants TO PUBLIC;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA runs TO PUBLIC;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA connectors TO PUBLIC;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA evidence TO PUBLIC;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA knowledge TO PUBLIC;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA system TO PUBLIC;

-- Grant sequence usage
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA system TO PUBLIC;

-- =====================================================================
-- COMMENTS (Documentation)
-- =====================================================================

COMMENT ON SCHEMA tenants IS 'Multi-tenant organization, users, and projects';
COMMENT ON SCHEMA runs IS 'Execution runs, steps, and results';
COMMENT ON SCHEMA connectors IS 'External data source integrations';
COMMENT ON SCHEMA evidence IS 'Graph-based evidence and relationships';
COMMENT ON SCHEMA knowledge IS 'Vector embeddings for semantic search';
COMMENT ON SCHEMA system IS 'Events, audit logs, and background jobs';

COMMENT ON TABLE tenants.tenants IS 'Root tenant entity with resource limits and usage tracking';
COMMENT ON TABLE knowledge.documents IS 'Vector embeddings for RAG using pgvector extension';
COMMENT ON TABLE system.event_queue IS 'Asynchronous event processing queue using LISTEN/NOTIFY';
