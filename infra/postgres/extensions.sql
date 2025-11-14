-- =====================================================================
-- PostgreSQL Extensions Initialization for Dyocense v4.0
-- =====================================================================
-- Purpose: Install and configure all required extensions
-- Image: timescale/timescaledb-ha:pg16 (includes TimescaleDB + pgvector)
-- Additional: Apache AGE, pg_cron, pg_stat_statements
-- =====================================================================

-- Core extensions (already in timescaledb-ha image)
CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;

CREATE EXTENSION IF NOT EXISTS vector CASCADE;

CREATE EXTENSION IF NOT EXISTS "uuid-ossp" CASCADE;

CREATE EXTENSION IF NOT EXISTS pgcrypto CASCADE;

CREATE EXTENSION IF NOT EXISTS pg_trgm CASCADE;

CREATE EXTENSION IF NOT EXISTS pg_stat_statements CASCADE;

-- Apache AGE for graph database capabilities
-- Note: Requires manual installation in container
-- Install command: apk add age && CREATE EXTENSION age CASCADE;
-- CREATE EXTENSION IF NOT EXISTS age CASCADE;

-- pg_cron for scheduled jobs
-- Note: Requires shared_preload_libraries configuration
-- CREATE EXTENSION IF NOT EXISTS pg_cron CASCADE;

-- =====================================================================
-- TimescaleDB Hypertables for Time-Series Data
-- =====================================================================

-- Business metrics (from Data-Architecture.md)
DO $$
BEGIN
  IF EXISTS (
    SELECT FROM information_schema.tables 
    WHERE table_schema = 'system' 
    AND table_name = 'business_metrics'
  ) THEN
    PERFORM create_hypertable(
      'system.business_metrics', 
      'created_at',
      chunk_time_interval => INTERVAL '7 days',
      if_not_exists => TRUE
    );
    
    -- Compression policy (compress data older than 30 days)
    PERFORM add_compression_policy(
      'system.business_metrics',
      INTERVAL '30 days',
      if_not_exists => TRUE
    );
    
    -- Retention policy (drop data older than 1 year)
    PERFORM add_retention_policy(
      'system.business_metrics',
      INTERVAL '365 days',
      if_not_exists => TRUE
    );
  END IF;
END$$;

-- Run execution history (from runs schema)
DO $$
BEGIN
  IF EXISTS (
    SELECT FROM information_schema.tables 
    WHERE table_schema = 'runs' 
    AND table_name = 'runs'
  ) THEN
    PERFORM create_hypertable(
      'runs.runs', 
      'started_at',
      chunk_time_interval => INTERVAL '7 days',
      if_not_exists => TRUE
    );
    
    -- Compression policy
    PERFORM add_compression_policy(
      'runs.runs',
      INTERVAL '30 days',
      if_not_exists => TRUE
    );
  END IF;
END$$;

-- LLM interaction logs (from evidence schema)
DO $$
BEGIN
  IF EXISTS (
    SELECT FROM information_schema.tables 
    WHERE table_schema = 'evidence' 
    AND table_name = 'llm_interactions'
  ) THEN
    PERFORM create_hypertable(
      'evidence.llm_interactions', 
      'timestamp',
      chunk_time_interval => INTERVAL '1 day',
      if_not_exists => TRUE
    );
    
    -- Compression policy
    PERFORM add_compression_policy(
      'evidence.llm_interactions',
      INTERVAL '14 days',
      if_not_exists => TRUE
    );
  END IF;
END$$;

-- =====================================================================
-- pgvector Indexes for Embeddings
-- =====================================================================

-- Knowledge base vector index (HNSW for fast similarity search)
DO $$
BEGIN
  IF EXISTS (
    SELECT FROM information_schema.columns 
    WHERE table_schema = 'knowledge' 
    AND table_name = 'documents'
    AND column_name = 'embedding'
  ) THEN
    CREATE INDEX IF NOT EXISTS idx_knowledge_documents_embedding_hnsw 
    ON knowledge.documents 
    USING hnsw (embedding vector_cosine_ops)
    WITH (m = 16, ef_construction = 64);
  END IF;
END$$;

-- Graph nodes vector index
DO $$
BEGIN
  IF EXISTS (
    SELECT FROM information_schema.columns 
    WHERE table_schema = 'knowledge' 
    AND table_name = 'graph_nodes'
    AND column_name = 'embedding'
  ) THEN
    CREATE INDEX IF NOT EXISTS idx_graph_nodes_embedding_hnsw 
    ON knowledge.graph_nodes 
    USING hnsw (embedding vector_cosine_ops)
    WITH (m = 16, ef_construction = 64);
  END IF;
END$$;

-- =====================================================================
-- Performance Indexes
-- =====================================================================

-- Tenant isolation indexes
CREATE INDEX IF NOT EXISTS idx_tenants_status ON tenants.tenants(status);
CREATE INDEX IF NOT EXISTS idx_tenants_plan_tier ON tenants.tenants(plan_tier);
CREATE INDEX IF NOT EXISTS idx_tenants_created_at ON tenants.tenants(created_at);

-- Run execution indexes
DO $$
BEGIN
  IF EXISTS (
    SELECT FROM information_schema.tables 
    WHERE table_schema = 'runs' 
    AND table_name = 'runs'
  ) THEN
    CREATE INDEX IF NOT EXISTS idx_runs_tenant_status 
    ON runs.runs(tenant_id, status);
    
    CREATE INDEX IF NOT EXISTS idx_runs_started_at 
    ON runs.runs(started_at DESC);
  END IF;
END$$;

-- Connector data indexes
DO $$
BEGIN
  IF EXISTS (
    SELECT FROM information_schema.tables 
    WHERE table_schema = 'connectors' 
    AND table_name = 'connections'
  ) THEN
    CREATE INDEX IF NOT EXISTS idx_connector_connections_tenant 
    ON connectors.connections(tenant_id);
    
    CREATE INDEX IF NOT EXISTS idx_connector_connections_status 
    ON connectors.connections(status);
  END IF;
END$$;

-- Knowledge JSONB indexes (GIN for flexible queries)
DO $$
BEGIN
  IF EXISTS (
    SELECT FROM information_schema.columns 
    WHERE table_schema = 'knowledge' 
    AND table_name = 'documents'
    AND column_name = 'metadata'
  ) THEN
    CREATE INDEX IF NOT EXISTS idx_knowledge_documents_metadata_gin 
    ON knowledge.documents USING gin (metadata jsonb_path_ops);
  END IF;
END$$;

-- Evidence JSONB indexes
DO $$
BEGIN
  IF EXISTS (
    SELECT FROM information_schema.columns 
    WHERE table_schema = 'evidence' 
    AND table_name = 'llm_interactions'
    AND column_name = 'context'
  ) THEN
    CREATE INDEX IF NOT EXISTS idx_evidence_llm_context_gin 
    ON evidence.llm_interactions USING gin (context jsonb_path_ops);
  END IF;
END$$;

-- =====================================================================
-- Row-Level Security (RLS) Setup
-- =====================================================================
-- Note: Detailed RLS policies should be in main schema.sql
-- This is just enabling RLS where needed

DO $$
DECLARE
  table_record RECORD;
BEGIN
  -- Enable RLS on all tenant-scoped tables
  FOR table_record IN 
    SELECT schemaname, tablename 
    FROM pg_tables 
    WHERE schemaname IN ('runs', 'connectors', 'evidence', 'knowledge')
  LOOP
    EXECUTE format('ALTER TABLE %I.%I ENABLE ROW LEVEL SECURITY', 
                   table_record.schemaname, 
                   table_record.tablename);
  END LOOP;
END$$;

-- =====================================================================
-- Statistics and Autovacuum Tuning
-- =====================================================================

-- Update statistics targets for frequently queried columns
ALTER TABLE tenants.tenants ALTER COLUMN tenant_id SET STATISTICS 1000;

ALTER TABLE tenants.tenants ALTER COLUMN status SET STATISTICS 500;

DO $$
BEGIN
  IF EXISTS (
    SELECT FROM information_schema.tables 
    WHERE table_schema = 'runs' 
    AND table_name = 'runs'
  ) THEN
    EXECUTE 'ALTER TABLE runs.runs ALTER COLUMN tenant_id SET STATISTICS 1000';
    EXECUTE 'ALTER TABLE runs.runs ALTER COLUMN status SET STATISTICS 500';
  END IF;
END$$;

-- Autovacuum tuning for high-traffic tables
DO $$
BEGIN
  IF EXISTS (
    SELECT FROM information_schema.tables 
    WHERE table_schema = 'evidence' 
    AND table_name = 'llm_interactions'
  ) THEN
    EXECUTE 'ALTER TABLE evidence.llm_interactions SET (
      autovacuum_vacuum_scale_factor = 0.01,
      autovacuum_analyze_scale_factor = 0.005
    )';

END IF;

END$$;

-- =====================================================================
-- Extension Configuration Complete
-- =====================================================================

-- Log extension status
DO $$
DECLARE
  ext_record RECORD;
BEGIN
  RAISE NOTICE 'Installed PostgreSQL Extensions:';
  FOR ext_record IN 
    SELECT extname, extversion 
    FROM pg_extension 
    ORDER BY extname
  LOOP
    RAISE NOTICE '  - % (version %)', ext_record.extname, ext_record.extversion;
  END LOOP;
END$$;