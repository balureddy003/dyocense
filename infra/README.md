# Dyocense External Services Infrastructure

Complete docker-compose setup for all external services required by Dyocense v4.0 backend services.

## 📋 Overview

This infrastructure provides:

- **PostgreSQL with TimescaleDB** - Time-series database with pgvector for embeddings
- **Complete Observability Stack** - Prometheus, Grafana, Loki, Jaeger
- **Optional Caching** - Redis for LLM response caching
- **Reverse Proxy** - Nginx for production deployments

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     External Services                        │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │  PostgreSQL  │  │    Redis     │  │    Nginx     │     │
│  │ TimescaleDB  │  │   (cache)    │  │   (proxy)    │     │
│  │  pgvector    │  │              │  │              │     │
│  └──────┬───────┘  └──────────────┘  └──────────────┘     │
│         │                                                   │
│  ┌──────▼────────────────────────────────────────────┐     │
│  │         Observability Stack                       │     │
│  ├───────────────────────────────────────────────────┤     │
│  │  Prometheus  │  Grafana  │  Loki  │  Jaeger      │     │
│  │  (metrics)   │  (dashb)  │ (logs) │ (tracing)    │     │
│  └───────────────────────────────────────────────────┘     │
│                                                              │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
                   Backend Services
              (Dyocense Kernel + Apps)
```

## 🚀 Quick Start

### 1. Configure Environment

```bash
# Copy example environment file
cp .env.external.example .env

# Edit .env and update passwords
nano .env
```

### 2. Start Services

**Development (PostgreSQL only)**

```bash
docker-compose -f docker-compose.external.yml up -d postgres
```

**Development + Caching**

```bash
docker-compose -f docker-compose.external.yml --profile cache up -d
```

**Development + Monitoring**

```bash
docker-compose -f docker-compose.external.yml --profile monitoring up -d
```

**Full Production Stack**

```bash
docker-compose -f docker-compose.external.yml --profile production up -d
```

### 3. Verify Services

```bash
# Check service health
docker-compose -f docker-compose.external.yml ps

# View logs
docker-compose -f docker-compose.external.yml logs -f
```

## 📊 Service Endpoints

| Service | URL | Default Port | Credentials |
|---------|-----|--------------|-------------|
| **PostgreSQL** | `postgresql://localhost:5432/dyocense` | 5432 | `dyocense` / (see .env) |
| **Grafana** | <http://localhost:3000> | 3000 | `admin` / `admin` |
| **Prometheus** | <http://localhost:9090> | 9090 | None (restrict in prod) |
| **Jaeger UI** | <http://localhost:16686> | 16686 | None |
| **Loki** | <http://localhost:3100> | 3100 | None (internal) |
| **Redis** | `redis://localhost:6379` | 6379 | (see .env) |

## 🔧 Configuration Files

### PostgreSQL

- `postgres/schema.sql` - Database schema (from existing)
- `postgres/extensions.sql` - Extension installation (TimescaleDB, pgvector, etc.)
- `postgres/postgresql.conf` - Performance tuning

### Prometheus

- `prometheus/prometheus.yml` - Scrape configuration
- `prometheus/alerts/system_alerts.yml` - Alert rules
- `prometheus/postgres_exporter_queries.yaml` - Custom PostgreSQL metrics

### Grafana

- `grafana/datasources/datasources.yml` - Auto-provision Prometheus, Loki, Jaeger
- `grafana/dashboards/dashboard-provider.yml` - Dashboard configuration

### Loki

- `loki/loki.yml` - Log aggregation configuration
- `promtail/promtail.yml` - Log shipping from Docker containers

### Nginx

- `nginx/nginx.conf` - Reverse proxy configuration

## 📦 Deployment Profiles

### Profile: `cache` (Development + Redis)

- PostgreSQL
- Redis (LLM caching)

### Profile: `monitoring` (Observability Stack)

- PostgreSQL
- Prometheus
- Grafana
- Loki + Promtail
- postgres-exporter

### Profile: `tracing` (Distributed Tracing)

- PostgreSQL
- Jaeger (all-in-one)

### Profile: `production` (Complete Stack)

- All services above
- Nginx reverse proxy
- Full resource limits
- Health checks

## 💰 Cost Estimates

| Deployment | vCPU | RAM | Disk | Monthly Cost (AWS/Azure) |
|------------|------|-----|------|--------------------------|
| **Minimal** (dev) | 1-2 | 1-2GB | 10GB | ~$20-40 |
| **With Monitoring** | 3-4 | 4-6GB | 50GB | ~$80-120 |
| **Full Production** | 6-8 | 8-10GB | 100GB | ~$150-250 |

*Compared to SaaS alternatives (Datadog + Managed DB): $500-2,400/month*

## 🔒 Security Checklist

### Before Production Deployment

- [ ] **Change all default passwords** in `.env`
- [ ] **Enable SSL/TLS** for PostgreSQL (uncomment in `postgresql.conf`)
- [ ] **Configure HTTPS** in nginx (uncomment SSL block)
- [ ] **Restrict Prometheus/Grafana access** (enable authentication)
- [ ] **Set up firewall rules** (only expose necessary ports)
- [ ] **Enable audit logging** in PostgreSQL
- [ ] **Configure automated backups** (PostgreSQL + Grafana)
- [ ] **Use secrets management** (AWS Secrets Manager, Vault, etc.)
- [ ] **Review Row-Level Security** policies in schema
- [ ] **Enable HSTS** and security headers in nginx

## 📈 Resource Requirements

### PostgreSQL (TimescaleDB)

- **Dev**: 1 CPU, 1GB RAM, 10GB disk
- **Prod**: 2-4 CPU, 4-8GB RAM, 100GB+ disk SSD

### Observability Stack

- **Prometheus**: 0.5-1 CPU, 256MB-1GB RAM, 20GB disk
- **Grafana**: 0.25-0.5 CPU, 128-512MB RAM, 1GB disk
- **Loki**: 0.25-1 CPU, 128-512MB RAM, 20GB disk
- **Jaeger**: 0.25-1 CPU, 256MB-1GB RAM, 10GB disk

### Redis (Optional)

- **Cache**: 0.25-1 CPU, 128-512MB RAM, 2GB disk

## 🛠️ Maintenance

### Backup PostgreSQL

```bash
# Create backup
docker-compose -f docker-compose.external.yml exec postgres \
  pg_dump -U dyocense dyocense > backup_$(date +%Y%m%d).sql

# Restore backup
docker-compose -f docker-compose.external.yml exec -T postgres \
  psql -U dyocense dyocense < backup_20240101.sql
```

### Update Services

```bash
# Pull latest images
docker-compose -f docker-compose.external.yml pull

# Restart services with new images
docker-compose -f docker-compose.external.yml up -d
```

### View Metrics

```bash
# PostgreSQL metrics
curl http://localhost:9187/metrics

# Prometheus metrics
curl http://localhost:9090/api/v1/query?query=up
```

## 🐛 Troubleshooting

### PostgreSQL won't start

```bash
# Check logs
docker-compose -f docker-compose.external.yml logs postgres

# Verify permissions
docker-compose -f docker-compose.external.yml exec postgres \
  ls -la /var/lib/postgresql/data
```

### Grafana dashboards not loading

```bash
# Restart Grafana
docker-compose -f docker-compose.external.yml restart grafana

# Check datasource connectivity
docker-compose -f docker-compose.external.yml exec grafana \
  curl http://prometheus:9090/-/healthy
```

### High disk usage

```bash
# Check volume sizes
docker system df -v

# Clean old logs (Loki retention: 30 days)
docker-compose -f docker-compose.external.yml exec loki \
  ls -lh /loki/chunks/
```

## 📚 Documentation References

- **PostgreSQL**: <https://www.postgresql.org/docs/16/>
- **TimescaleDB**: <https://docs.timescale.com/>
- **pgvector**: <https://github.com/pgvector/pgvector>
- **Prometheus**: <https://prometheus.io/docs/>
- **Grafana**: <https://grafana.com/docs/>
- **Loki**: <https://grafana.com/docs/loki/>
- **Jaeger**: <https://www.jaegertracing.io/docs/>

## 🔗 Integration with Dyocense Kernel

The kernel service expects the following environment variables:

```bash
# Database
DATABASE_URL=postgresql://dyocense:password@postgres:5432/dyocense

# Redis (optional)
REDIS_URL=redis://:password@redis:6379/0

# OpenTelemetry (Jaeger)
OTEL_EXPORTER_OTLP_ENDPOINT=http://jaeger:4318
OTEL_SERVICE_NAME=dyocense-kernel

# Prometheus metrics
PROMETHEUS_METRICS_ENABLED=true
PROMETHEUS_METRICS_PORT=8001
```

See `docker-compose.smb.yml` for kernel service configuration.

---

## Legacy Kubernetes Setup (Phase 4)

Phase 4 introduced Kubernetes manifests (now deprecated in favor of docker-compose for v4.0):

- `k8s/base/` — Kustomize base including namespace, MongoDB (StatefulSet), Keycloak, NATS
- `docker-compose/` — Local stack (legacy)

**Note**: v4.0 uses PostgreSQL (not MongoDB) and docker-compose (not Kubernetes) for cost optimization.

## 📄 License

Part of Dyocense v4.0 - See project LICENSE
