# 🔄 Data Pipeline Architecture

**Version:** 4.0 (PostgreSQL pg_cron + ConnectorService)  
**Last Updated:** November 14, 2025  
**Status:** Active Development

---

## 📋 Table of Contents

1. [Overview](#1-overview)
2. [Pipeline Stages](#2-pipeline-stages)
3. [Connector Service](#3-connector-service)
4. [Scheduling (pg_cron)](#4-scheduling-pg_cron)
5. [Data Validation](#5-data-validation)
6. [Migration from Airflow](#6-migration-from-airflow)

---

## 🎯 1. Overview

### **Data Pipeline Philosophy**

> **"ELT over ETL: Load raw data, transform in PostgreSQL"**

**Why ELT?**

- ✅ **Flexibility:** Transform data multiple times without re-ingesting
- ✅ **PostgreSQL Power:** Use SQL for transformations (faster than Python)
- ✅ **Auditability:** Raw data preserved, transformations versioned in Git

---

### **v3.0 vs. v4.0 Comparison**

| Component | v3.0 (Microservices) | v4.0 (Monolith) | Savings |
|-----------|---------------------|----------------|---------|
| **Orchestrator** | Apache Airflow (managed) | pg_cron (PostgreSQL built-in) | **$200/mo** |
| **Workflow Engine** | Temporal | PostgreSQL functions + pg_cron | **$150/mo** |
| **Validation** | Great Expectations (separate service) | SQL CHECK constraints + triggers | $0 |
| **Transformation** | DBT (separate layer) | PostgreSQL views + functions | $0 |
| **Connector Service** | Standalone microservice | Module in monolith | $0 |

**Total Savings:** $350/month ($4,200/year)

---

## 🔄 2. Pipeline Stages

### **Stage 1: Ingestion**

**Connectors → Raw Data Schema**

```sql
-- Raw data table (schema-on-read)
CREATE TABLE raw_connector_data (
    raw_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    connector_id UUID NOT NULL REFERENCES connectors(connector_id),
    
    source_type TEXT NOT NULL,  -- "salesforce", "shopify", "csv", "api"
    source_record_id TEXT,  -- External ID (for idempotency)
    
    data JSONB NOT NULL,  -- Raw JSON payload
    
    ingested_at TIMESTAMPTZ DEFAULT NOW(),
    processed BOOLEAN DEFAULT FALSE,
    
    UNIQUE(connector_id, source_record_id)  -- Prevent duplicates
);

CREATE INDEX idx_raw_tenant ON raw_connector_data(tenant_id, ingested_at);
CREATE INDEX idx_raw_processed ON raw_connector_data(processed) WHERE NOT processed;
```

---

### **Stage 2: Validation**

**SQL CHECK Constraints + Triggers**

```sql
-- Parsed metrics table
CREATE TABLE metrics (
    metric_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    
    metric_type TEXT NOT NULL,  -- "revenue", "inventory", "staffing"
    metric_value NUMERIC NOT NULL,
    metric_date DATE NOT NULL,
    
    -- Validation constraints
    CONSTRAINT valid_metric_value CHECK (metric_value >= 0),
    CONSTRAINT valid_metric_type CHECK (metric_type IN ('revenue', 'inventory', 'staffing', 'costs')),
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    
    UNIQUE(tenant_id, metric_type, metric_date)  -- One value per metric per day
);

-- Validation trigger
CREATE OR REPLACE FUNCTION validate_metric() RETURNS TRIGGER AS $$
BEGIN
    -- Check data freshness (no future dates)
    IF NEW.metric_date > CURRENT_DATE THEN
        RAISE EXCEPTION 'Metric date cannot be in the future: %', NEW.metric_date;
    END IF;
    
    -- Check outliers (revenue > 1M needs review)
    IF NEW.metric_type = 'revenue' AND NEW.metric_value > 1000000 THEN
        INSERT INTO data_quality_alerts (tenant_id, metric_id, alert_type, message)
        VALUES (NEW.tenant_id, NEW.metric_id, 'outlier', 
                'Revenue value unusually high: ' || NEW.metric_value);
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER validate_metric_trigger
BEFORE INSERT OR UPDATE ON metrics
FOR EACH ROW EXECUTE FUNCTION validate_metric();
```

---

### **Stage 3: Transformation**

**PostgreSQL Views + Materialized Views**

```sql
-- Daily revenue by category
CREATE VIEW daily_revenue_by_category AS
SELECT 
    tenant_id,
    metric_date,
    (data->>'category')::TEXT AS category,
    SUM(metric_value) AS total_revenue
FROM metrics
WHERE metric_type = 'revenue'
GROUP BY tenant_id, metric_date, category;

-- Monthly aggregates (materialized for performance)
CREATE MATERIALIZED VIEW monthly_revenue AS
SELECT 
    tenant_id,
    DATE_TRUNC('month', metric_date) AS month,
    SUM(metric_value) AS total_revenue,
    AVG(metric_value) AS avg_daily_revenue,
    COUNT(*) AS days_with_data
FROM metrics
WHERE metric_type = 'revenue'
GROUP BY tenant_id, DATE_TRUNC('month', metric_date);

CREATE INDEX idx_monthly_revenue ON monthly_revenue(tenant_id, month);

-- Refresh materialized view daily
SELECT cron.schedule(
    'refresh-monthly-revenue',
    '0 1 * * *',  -- Daily at 1 AM
    'REFRESH MATERIALIZED VIEW monthly_revenue;'
);
```

---

### **Stage 4: Availability**

**REST APIs (FastAPI)**

```python
@router.get("/metrics/{tenant_id}")
async def get_metrics(
    tenant_id: str,
    metric_type: str,
    start_date: date,
    end_date: date,
    db: Session = Depends(get_db)
):
    """Get metrics with flexible filters"""
    
    query = db.query(Metric).filter(
        Metric.tenant_id == tenant_id,
        Metric.metric_type == metric_type,
        Metric.metric_date >= start_date,
        Metric.metric_date <= end_date
    )
    
    metrics = query.all()
    
    return {
        "metrics": [m.to_dict() for m in metrics],
        "count": len(metrics),
        "period": {"start": start_date, "end": end_date}
    }
```

---

## 🔌 3. Connector Service

### **Supported Connectors**

| Type | Examples | Frequency |
|------|----------|-----------|
| **API-Based** | Salesforce, Shopify, Square | Hourly |
| **Database** | ERPNext, QuickBooks (SQL query) | Daily |
| **File Upload** | CSV, Excel | On-demand |
| **Webhook** | Real-time (Stripe events) | Event-driven |

---

### **Connector Configuration**

```sql
CREATE TABLE connectors (
    connector_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    
    name TEXT NOT NULL,
    type TEXT NOT NULL,  -- "salesforce", "csv", "api", "webhook"
    
    -- Auth credentials (encrypted)
    credentials JSONB NOT NULL,  -- {"api_key": "...", "instance_url": "..."}
    
    -- Sync config
    sync_frequency TEXT DEFAULT 'hourly',  -- "hourly", "daily", "weekly", "manual"
    last_sync_at TIMESTAMPTZ,
    next_sync_at TIMESTAMPTZ,
    
    status TEXT DEFAULT 'active',  -- "active", "paused", "error"
    error_message TEXT,
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_connectors_tenant ON connectors(tenant_id);
CREATE INDEX idx_connectors_next_sync ON connectors(next_sync_at) WHERE status = 'active';
```

---

### **Connector Implementation**

```python
from abc import ABC, abstractmethod

class BaseConnector(ABC):
    def __init__(self, connector_config: dict):
        self.connector_id = connector_config["connector_id"]
        self.tenant_id = connector_config["tenant_id"]
        self.credentials = connector_config["credentials"]
    
    @abstractmethod
    async def fetch_data(self, since: datetime) -> List[dict]:
        """Fetch data since last sync"""
        pass
    
    async def sync(self, db: Session):
        """Run full sync cycle"""
        # Get last sync timestamp
        connector = db.query(Connector).filter_by(connector_id=self.connector_id).first()
        since = connector.last_sync_at or (datetime.utcnow() - timedelta(days=30))
        
        try:
            # Fetch data
            records = await self.fetch_data(since)
            
            # Insert into raw_connector_data
            for record in records:
                raw_data = RawConnectorData(
                    tenant_id=self.tenant_id,
                    connector_id=self.connector_id,
                    source_type=connector.type,
                    source_record_id=record.get("id"),
                    data=record
                )
                db.add(raw_data)
            
            # Update connector status
            connector.last_sync_at = datetime.utcnow()
            connector.next_sync_at = self.calculate_next_sync(connector.sync_frequency)
            connector.status = "active"
            connector.error_message = None
            
            db.commit()
            
        except Exception as e:
            connector.status = "error"
            connector.error_message = str(e)
            db.commit()
            raise
```

---

### **Salesforce Connector Example**

```python
from simple_salesforce import Salesforce

class SalesforceConnector(BaseConnector):
    async def fetch_data(self, since: datetime) -> List[dict]:
        # Authenticate
        sf = Salesforce(
            username=self.credentials["username"],
            password=self.credentials["password"],
            security_token=self.credentials["security_token"]
        )
        
        # SOQL query
        query = f"""
        SELECT Id, Amount, CloseDate, StageName
        FROM Opportunity
        WHERE LastModifiedDate >= {since.isoformat()}
        """
        
        results = sf.query_all(query)
        return results["records"]
```

---

## ⏰ 4. Scheduling (pg_cron)

### **Why pg_cron?**

| Feature | Apache Airflow | pg_cron | Winner |
|---------|---------------|---------|--------|
| **Cost** | $200/mo (managed) | Free | ✅ pg_cron |
| **Complexity** | High (separate service) | Low (PostgreSQL extension) | ✅ pg_cron |
| **DAG UI** | ✅ Yes | ❌ No | Airflow |
| **Use Case** | Complex workflows | Simple scheduled jobs | - |

**Verdict:** pg_cron for v4.0 (simple SMB pipelines), migrate to Airflow if >1000 connectors

---

### **Install pg_cron**

```sql
-- Enable extension
CREATE EXTENSION IF NOT EXISTS pg_cron;

-- Grant permissions
GRANT USAGE ON SCHEMA cron TO dyocense_user;
```

---

### **Schedule Connector Syncs**

```sql
-- Hourly: Sync all active connectors
SELECT cron.schedule(
    'sync-hourly-connectors',
    '0 * * * *',  -- Every hour
    $$
    SELECT connector_service_sync(connector_id)
    FROM connectors
    WHERE status = 'active'
      AND sync_frequency = 'hourly'
      AND next_sync_at <= NOW();
    $$
);

-- Daily: Sync daily connectors
SELECT cron.schedule(
    'sync-daily-connectors',
    '0 2 * * *',  -- Daily at 2 AM
    $$
    SELECT connector_service_sync(connector_id)
    FROM connectors
    WHERE status = 'active'
      AND sync_frequency = 'daily'
      AND next_sync_at <= NOW();
    $$
);
```

---

### **Connector Sync Function**

```sql
CREATE OR REPLACE FUNCTION connector_service_sync(p_connector_id UUID)
RETURNS VOID AS $$
DECLARE
    v_tenant_id UUID;
    v_type TEXT;
BEGIN
    -- Get connector details
    SELECT tenant_id, type INTO v_tenant_id, v_type
    FROM connectors WHERE connector_id = p_connector_id;
    
    -- Call Python connector via pg_net (HTTP trigger to FastAPI)
    PERFORM net.http_post(
        url := 'http://localhost:8000/internal/sync-connector',
        body := json_build_object(
            'connector_id', p_connector_id,
            'tenant_id', v_tenant_id
        )::text
    );
END;
$$ LANGUAGE plpgsql;
```

---

### **FastAPI Sync Endpoint**

```python
@router.post("/internal/sync-connector")
async def sync_connector(request: dict, db: Session = Depends(get_db)):
    """Trigger connector sync (called by pg_cron)"""
    
    connector_id = request["connector_id"]
    connector = db.query(Connector).filter_by(connector_id=connector_id).first()
    
    # Instantiate connector
    if connector.type == "salesforce":
        conn = SalesforceConnector(connector.to_dict())
    elif connector.type == "shopify":
        conn = ShopifyConnector(connector.to_dict())
    else:
        raise ValueError(f"Unsupported connector type: {connector.type}")
    
    # Run sync
    await conn.sync(db)
    
    return {"status": "success", "connector_id": connector_id}
```

---

## ✅ 5. Data Validation

### **Data Quality Alerts**

```sql
CREATE TABLE data_quality_alerts (
    alert_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    metric_id UUID REFERENCES metrics(metric_id),
    
    alert_type TEXT NOT NULL,  -- "outlier", "missing", "schema_error"
    severity TEXT DEFAULT 'warning',  -- "info", "warning", "critical"
    message TEXT NOT NULL,
    
    resolved BOOLEAN DEFAULT FALSE,
    resolved_at TIMESTAMPTZ,
    
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_dq_alerts ON data_quality_alerts(tenant_id, created_at) WHERE NOT resolved;
```

---

### **Validation Rules**

```sql
-- Check for missing days (data should be continuous)
SELECT cron.schedule(
    'check-missing-data',
    '0 3 * * *',  -- Daily at 3 AM
    $$
    WITH expected_dates AS (
        SELECT 
            tenant_id,
            generate_series(
                CURRENT_DATE - INTERVAL '30 days',
                CURRENT_DATE - INTERVAL '1 day',
                INTERVAL '1 day'
            )::DATE AS expected_date
        FROM tenants
    ),
    actual_dates AS (
        SELECT DISTINCT tenant_id, metric_date
        FROM metrics
        WHERE metric_date >= CURRENT_DATE - INTERVAL '30 days'
    )
    INSERT INTO data_quality_alerts (tenant_id, alert_type, severity, message)
    SELECT 
        e.tenant_id,
        'missing' AS alert_type,
        'warning' AS severity,
        'Missing data for date: ' || e.expected_date AS message
    FROM expected_dates e
    LEFT JOIN actual_dates a ON e.tenant_id = a.tenant_id AND e.expected_date = a.metric_date
    WHERE a.metric_date IS NULL;
    $$
);
```

---

## 🚀 6. Migration from Airflow

### **Migration Strategy**

**For <100 Tenants:**

1. ✅ Use pg_cron (simple, free)
2. ✅ Manual monitoring (Grafana dashboards)

**For 100-1000 Tenants:**

1. 🟡 Hybrid: pg_cron + cron monitoring
2. 🟡 Add retry logic in Python

**For >1000 Tenants:**

1. 🔴 Migrate to Apache Airflow
2. 🔴 Use dynamic DAG generation
3. 🔴 Add backfill capabilities

---

### **Airflow DAG (for future migration)**

```python
from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta

default_args = {
    'owner': 'dyocense',
    'retries': 3,
    'retry_delay': timedelta(minutes=5),
}

with DAG(
    'sync_all_connectors',
    default_args=default_args,
    schedule_interval='0 * * * *',  # Hourly
    start_date=datetime(2024, 11, 1),
    catchup=False
) as dag:
    
    def sync_connector(connector_id: str):
        import requests
        response = requests.post(
            "http://localhost:8000/internal/sync-connector",
            json={"connector_id": connector_id}
        )
        response.raise_for_status()
    
    # Dynamically generate tasks for each connector
    connectors = get_active_connectors()  # Query PostgreSQL
    
    for connector in connectors:
        task = PythonOperator(
            task_id=f'sync_{connector["connector_id"]}',
            python_callable=sync_connector,
            op_kwargs={'connector_id': connector["connector_id"]}
        )
```

---

## 🎯 Next Steps

1. **Review [Service Architecture](./Service-Architecture.md)** for ConnectorService module
2. **Review [Data Architecture](./Data-Architecture.md)** for raw data schema
3. **Start Week 3** of [Implementation Roadmap](./Implementation-Roadmap.md)

**Simple pipelines, powerful insights! 🔄**
