# 📖 Dyocense Documentation Guide

**Version:** 4.0 (Cost-Optimized Monolith)  
**Last Updated:** November 14, 2025  
**Status:** Active Development

---

## 🎯 What is Dyocense?

**Dyocense** is a **Business AI Fitness Coach** for small and medium businesses (SMBs). Unlike traditional BI tools that just visualize data, Dyocense:

- 🤖 **Coaches SMBs** on what to do next (not just what happened)
- 🧮 **Optimizes** operations using mathematical solvers (inventory, staffing, pricing)
- 📈 **Forecasts** future outcomes with uncertainty quantification
- 🔍 **Explains** why metrics changed using causal inference
- 💰 **Costs <$30/month** per company (vs. $500-1500 for traditional BI)

---

## 🗺️ Documentation Reading Order

### **New to the Project? Start Here:**

1. **[Executive Summary](./Executive-Summary.md)** ← Start here for business context
2. **[Implementation Roadmap](./Implementation-Roadmap.md)** ← 12-week plan to MVP
3. **[Design Document](./Design-Document.md)** ← Overall system design

### **Architecture Deep Dives:**

4. **[Service Architecture](./Service-Architecture.md)** ← Monolithic backend structure
5. **[Data Architecture](./Data-Architecture.md)** ← PostgreSQL schema design
6. **[Technology Stack Selection](./Technology Stack Selection.md)** ← Why we chose each tool
7. **[AI & Analytics Stack](./AI & Analytics Stack.md)** ← LLMs + optimization + forecasting
8. **[Multi-Agent System Design](./Multi-Agent System Design.md)** ← Coach agent architecture

### **Cross-Cutting Concerns:**

9. **[Security & Multi-Tenancy](./Security & Multi-Tenancy.md)** ← Row-Level Security (RLS)
10. **[Observability Architecture](./Observability Architecture.md)** ← Prometheus + Grafana
11. **[Data Pipeline Architecture](./Data Pipeline Architecture.md)** ← ETL design

---

## 🏗️ Architecture Decision (v4.0 Changes)

### **Why We Simplified to a Monolith**

| **Old Approach (v1-3)** | **New Approach (v4.0)** | **Why?** |
|------------------------|------------------------|----------|
| 19 microservices | Single FastAPI monolith | 80% reduction in ops complexity |
| Separate vector DB (Pinecone $200/mo) | pgvector in PostgreSQL | $200/month savings |
| Separate graph DB (Neo4j $500/mo) | Apache AGE in PostgreSQL | $500/month savings |
| Cloud-only LLMs ($5/100 queries) | 70% local Llama, 30% cloud | 80% cost reduction |
| Kubernetes required | Docker Compose for <5000 SMBs | Vertical scaling first |
| 19 deployment pipelines | Single deployment | Faster iterations |

**Result:** Infrastructure costs drop from **$5/tenant/month** to **<$1/tenant/month**.

---

## 🚀 Quick Start (Local Development)

### **Prerequisites**

- Docker Desktop 4.25+
- Python 3.11+
- Node.js 18+
- PostgreSQL 16+ (via Docker)

### **1. Clone & Setup**

```bash
git clone https://github.com/balureddy003/dyocense.git
cd dyocense

# Install Python dependencies
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt

# Install Node dependencies (for frontend)
npm install
```

### **2. Start PostgreSQL with Extensions**

```bash
docker-compose -f docker-compose.smb.yml up -d postgres

# Wait for PostgreSQL to be ready
docker exec -it dyocense-postgres pg_isready
```

### **3. Run Database Migrations**

```bash
# Create extensions
psql -h localhost -U dyocense -d dyocense_db -c "CREATE EXTENSION IF NOT EXISTS timescaledb;"
psql -h localhost -U dyocense -d dyocense_db -c "CREATE EXTENSION IF NOT EXISTS vector;"
psql -h localhost -U dyocense -d dyocense_db -c "LOAD 'age';"

# Run schema migrations
python scripts/run_migration.py
```

### **4. Start Backend (Monolith)**

```bash
cd backend
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

### **5. Start Frontend**

```bash
cd apps/smb
npm run dev
```

### **6. Access the Application**

- **Frontend:** <http://localhost:3000>
- **Backend API Docs:** <http://localhost:8000/docs>
- **Grafana (Observability):** <http://localhost:3001>

---

## 📊 Deployment Scenarios

### **Scenario 1: Bootstrap (1-50 SMBs)**

**Cost:** ~$55/month  
**Infrastructure:**

- Single DigitalOcean droplet (8 vCPU, 32GB RAM): $48/month
- CloudFlare CDN (free tier): $0
- Backblaze B2 storage (10GB backups): $0.50/month
- Upstash Redis (free tier): $0
- Local Llama 3 8B (on same droplet): $0
- Cloud LLM (30% of queries): ~$5/month

**Per-Tenant Cost:** $1.10/tenant/month (for 50 SMBs)

### **Scenario 2: Growth (50-500 SMBs)**

**Cost:** ~$280/month  
**Infrastructure:**

- Hetzner dedicated server (16 vCPU, 64GB RAM): $120/month
- PostgreSQL managed backup (Hetzner): $20/month
- CloudFlare CDN + DDoS protection: $20/month
- Redis (Upstash paid tier): $10/month
- Local Llama 3 70B (GPU droplet): $80/month
- Cloud LLM (30% of queries): ~$30/month

**Per-Tenant Cost:** $0.56/tenant/month (for 500 SMBs)

### **Scenario 3: Scale (500-5000 SMBs)**

**Cost:** ~$1500-3000/month  
**Infrastructure:**

- Kubernetes cluster (3 nodes, 64 vCPU total): $800/month
- PostgreSQL with read replicas (3 instances): $400/month
- Redis cluster (high availability): $100/month
- CloudFlare enterprise: $200/month
- Local LLM inference cluster (4 GPUs): $600/month
- Cloud LLM (30% of queries): ~$200/month

**Per-Tenant Cost:** $0.30-0.60/tenant/month (for 5000 SMBs)

---

## 🎯 Success Metrics

### **Business KPIs**

- **Customer Acquisition Cost (CAC):** <$500 per SMB
- **Monthly Recurring Revenue (MRR) per Customer:** $15-149 (tiered pricing)
- **Gross Margin:** >95% (infrastructure costs <5% of revenue)
- **Churn Rate:** <5% monthly
- **Net Revenue Retention:** >110% (upsells + expansions)

### **Technical KPIs**

- **API Response Time (p95):** <500ms
- **Coach Query Latency (p95):** <3 seconds
- **Database Query Time (p95):** <100ms
- **System Uptime:** >99.9%
- **Cost per Request:** <$0.001

### **Product KPIs**

- **Daily Active Users (DAU):** >60% of customers
- **Goals Created per User:** >3 per month
- **Coach Interactions per User:** >10 per week
- **Recommendations Accepted:** >40%

---

## 🛠️ Development Workflow

### **Branching Strategy**

```
main (production)
  └─ develop (integration)
       └─ feature/* (feature branches)
       └─ fix/* (bug fixes)
```

### **Testing Pyramid**

1. **Unit Tests** (70%): `pytest tests/unit/`
2. **Integration Tests** (20%): `pytest tests/integration/`
3. **E2E Tests** (10%): `pytest tests/e2e/`

### **Code Quality Gates**

- **Pre-commit hooks:** Black, isort, flake8, mypy
- **CI/CD:** GitHub Actions (lint → test → build → deploy)
- **Coverage requirement:** >80%

---

## 📞 Support & Contributions

- **Issues:** [GitHub Issues](https://github.com/balureddy003/dyocense/issues)
- **Discussions:** [GitHub Discussions](https://github.com/balureddy003/dyocense/discussions)
- **Slack:** (Internal team only)

---

## 📝 Next Steps

1. Read **[Executive Summary](./Executive-Summary.md)** to understand the business case
2. Review **[Implementation Roadmap](./Implementation-Roadmap.md)** for the 12-week plan
3. Check **[Design Document](./Design-Document.md)** for architecture overview
4. Dive into specific architecture docs based on your focus area

**Happy building! 🚀**
