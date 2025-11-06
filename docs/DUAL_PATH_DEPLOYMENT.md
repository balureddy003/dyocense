# Dyocense Dual-Path Deployment Strategy

## Overview

Dyocense now supports **two deployment modes** to serve different customer segments while maintaining a single codebase:

1. **SMB Mode** - Simplified stack for small businesses (primary focus)
2. **Platform Mode** - Full enterprise stack with all advanced features

This architecture allows us to:
- ✅ Focus on SMB customers with simplified UX and lower costs
- ✅ Preserve platform capabilities for enterprise upsell
- ✅ Make faster decisions in SMB mode (fewer dependencies)
- ✅ Maintain single codebase (no forking)

---

## 🎯 Mode Comparison

| Feature | SMB Mode | Platform Mode |
|---------|----------|---------------|
| **Target Customer** | Small businesses (1-10 locations) | Enterprise (10+ locations, dev teams) |
| **Monthly Cost** | $50-200 | $500-2000+ |
| **Complexity** | Low | High |
| **Setup Time** | 5 minutes | 1-2 hours |
| **Dependencies** | MongoDB + LLM | MongoDB + Neo4j + Qdrant + Keycloak + LLM |
| **Authentication** | Simple JWT | Keycloak (SSO, SAML) |
| **Evidence Graph** | ❌ | ✅ Neo4j |
| **Vector Search** | ❌ | ✅ Qdrant |
| **Solver Options** | OR-Tools only | OR-Tools + Gurobi + HiGHS |
| **Transactions** | ❌ | ✅ |
| **API Access** | Growth tier+ | All tiers |

---

## 🚀 Quick Start

### Deploy SMB Mode (Recommended for Launch)

```bash
# 1. Copy SMB environment config
cp .env.smb .env

# 2. Update credentials
nano .env  # Set MongoDB URI, Azure OpenAI keys

# 3. Install dependencies
pip install -r requirements-dev.txt

# 4. Run migrations (if needed)
python scripts/init_db.py

# 5. Start server
PYTHONPATH=. uvicorn services.kernel.main:app --reload --port 8001
```

**Environment Variables:**
```bash
DEPLOYMENT_MODE=smb
USE_MONGODB=true
USE_NEO4J=false
USE_QDRANT=false
USE_KEYCLOAK=false
```

**Infrastructure Needed:**
- MongoDB Atlas (M0 free tier or M10 at $57/month)
- Azure OpenAI or OpenAI API
- Hosting: Railway, Render, Fly.io ($20-50/month)

**Total Monthly Cost: ~$100-200**

---

### Deploy Platform Mode (For Enterprise Customers)

```bash
# 1. Copy Platform environment config
cp .env.platform .env

# 2. Update all service credentials
nano .env  # Set MongoDB, Neo4j, Qdrant, Keycloak

# 3. Deploy infrastructure
cd infra/k8s
kubectl apply -f namespace.yaml
kubectl apply -f mongodb/
kubectl apply -f neo4j/
kubectl apply -f qdrant/
kubectl apply -f keycloak/

# 4. Run migrations
python scripts/init_db.py
python scripts/init_neo4j.py

# 5. Deploy application
kubectl apply -f deployments/
```

**Environment Variables:**
```bash
DEPLOYMENT_MODE=platform
USE_MONGODB=true
USE_NEO4J=true
USE_QDRANT=true
USE_KEYCLOAK=true
ENABLE_EVIDENCE_GRAPH=true
ENABLE_VECTOR_SEARCH=true
```

**Infrastructure Needed:**
- MongoDB Atlas M30+ ($200-500/month)
- Neo4j Aura Professional ($200-500/month)
- Qdrant Cloud ($100-300/month)
- Keycloak (self-hosted or managed)
- Kubernetes cluster ($300-1000/month)

**Total Monthly Cost: ~$1000-2500**

---

## 🏗️ Architecture Differences

### SMB Mode Architecture

```
┌─────────────────────────────────────────┐
│          React Frontend (UI)             │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│         FastAPI Backend (Kernel)         │
│  ┌──────────┬──────────┬──────────┐     │
│  │Compiler  │Optimizer │Explainer │     │
│  └────┬─────┴────┬─────┴────┬─────┘     │
│       │          │          │           │
│  ┌────▼──────────▼──────────▼─────┐     │
│  │     LLM (Azure OpenAI/OpenAI)   │     │
│  └─────────────────────────────────┘     │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│          MongoDB (Single DB)             │
│  • Tenants  • Projects  • Playbooks     │
│  • Users    • Evidence  • Config        │
└──────────────────────────────────────────┘

Fast decisions • Low cost • Simple ops
```

### Platform Mode Architecture

```
┌─────────────────────────────────────────┐
│          React Frontend (UI)             │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│         FastAPI Backend (Kernel)         │
│  ┌──────┬──────┬──────┬───────┬──────┐  │
│  │Comp  │Optim │Expl  │Policy │Diag  │  │
│  └──┬───┴──┬───┴──┬───┴───┬───┴──┬───┘  │
│     │      │      │       │      │      │
│  ┌──▼──────▼──────▼───────▼──────▼───┐  │
│  │         LLM + Knowledge Base        │  │
│  └─────────────────────────────────────┘  │
└──┬──────────┬──────────┬────────────┬────┘
   │          │          │            │
┌──▼────┐ ┌──▼────┐ ┌───▼──────┐ ┌───▼────────┐
│MongoDB│ │Neo4j  │ │Qdrant    │ │Keycloak    │
│       │ │Evidence│ │Vector    │ │Auth & SSO  │
│Data   │ │Graph  │ │Search    │ │            │
└───────┘ └───────┘ └──────────┘ └────────────┘

Full audit • Semantic search • Enterprise auth
```

---

## 💰 Pricing Strategy Alignment

### SMB Mode → SMB Pricing Tiers

| Tier | Price | Target | Deployment |
|------|-------|--------|------------|
| **Starter** | $49/mo | 1 location | SMB Mode |
| **Growth** | $199/mo | 3 locations | SMB Mode |
| **Business** | $499/mo | 10 locations | SMB Mode |

**Features enabled:**
- Simple JWT auth
- Basic OR solver (OR-Tools)
- MongoDB persistence
- Email support → Dedicated manager

### Platform Mode → Enterprise Tier

| Tier | Price | Target | Deployment |
|------|-------|--------|------------|
| **Enterprise** | $1999+/mo | Unlimited | Platform Mode |

**Additional features:**
- Keycloak SSO (SAML, SCIM)
- Neo4j evidence graph
- Qdrant semantic search
- Advanced solvers (Gurobi)
- 24/7 support + solution architect
- On-premise option

---

## 🔧 Code Changes for Dual-Path

### 1. Feature Flags (Automatic)

```python
from packages.kernel_common.config import get_config

config = get_config()

# Check deployment mode
if config.features.is_smb_mode():
    # Use simplified components
    use_simple_auth()
    use_ortools_only()
    skip_evidence_graph()
    
elif config.features.is_platform_mode():
    # Use full stack
    use_keycloak_auth()
    use_advanced_solvers()
    enable_evidence_graph()
```

### 2. Evidence Service (Auto-disabled in SMB)

```python
from packages.kernel_common.config import get_config

config = get_config()

if config.features.enable_evidence_graph:
    # Platform mode: Use Neo4j
    from packages.trust.graph_store import Neo4jGraphStore
    graph_store = Neo4jGraphStore()
else:
    # SMB mode: Use stub
    from packages.trust.graph_store import NullGraphStore
    graph_store = NullGraphStore()
```

### 3. Auth Strategy (Auto-selected)

```python
from packages.kernel_common.config import get_config

config = get_config()

if config.features.use_keycloak:
    # Platform mode: Keycloak SSO
    from packages.kernel_common.keycloak_auth import validate_keycloak_token
    validate_token = validate_keycloak_token
else:
    # SMB mode: Simple JWT
    from packages.kernel_common.auth import validate_bearer_token
    validate_token = validate_bearer_token
```

---

## 📊 Migration Path

### SMB → Platform Upgrade

When a customer outgrows SMB tier:

1. **Trigger:** Customer hits Business tier limits or requests enterprise features
2. **Process:**
   ```bash
   # 1. Backup SMB data
   python scripts/backup_mongodb.py --output smb_backup.json
   
   # 2. Deploy platform infrastructure
   cd infra/k8s && kubectl apply -f .
   
   # 3. Migrate data
   python scripts/migrate_smb_to_platform.py --backup smb_backup.json
   
   # 4. Enable platform features
   export DEPLOYMENT_MODE=platform
   
   # 5. Restart services
   kubectl rollout restart deployment/dyocense-kernel
   ```
3. **Timeline:** 2-4 hours with zero data loss
4. **Pricing:** Upgrade to Enterprise tier ($1999/mo)

---

## 🧪 Testing Both Modes

### Test SMB Mode

```bash
# Set SMB environment
export DEPLOYMENT_MODE=smb
export USE_NEO4J=false
export USE_QDRANT=false
export USE_KEYCLOAK=false

# Run tests
pytest tests/ -k "smb" --verbose
```

### Test Platform Mode

```bash
# Set Platform environment
export DEPLOYMENT_MODE=platform
export USE_NEO4J=true
export USE_QDRANT=true
export USE_KEYCLOAK=true

# Run tests
pytest tests/ -k "platform" --verbose
```

### Test Both Modes

```bash
# Run full test suite
./scripts/test_both_modes.sh
```

---

## 🎯 Benefits of Dual-Path Approach

### Business Benefits

✅ **Faster GTM:** Launch SMB product in weeks, not months  
✅ **Lower CAC:** Simplified product = easier to sell  
✅ **Higher Margins:** SMB mode costs 80% less to operate  
✅ **Clear Upsell:** Natural upgrade path to enterprise  
✅ **Market Segmentation:** Different products for different buyers

### Technical Benefits

✅ **Single Codebase:** No forking or parallel development  
✅ **Feature Flags:** Switch modes with environment variable  
✅ **Graceful Fallbacks:** All platform features degrade gracefully  
✅ **Easy Testing:** Test both modes in CI/CD  
✅ **Migration Path:** Proven upgrade process

### Customer Benefits

✅ **SMB Customers:** Simple, affordable, fast time-to-value  
✅ **Enterprise Customers:** Full power, audit trails, integrations  
✅ **Smooth Upgrade:** Keep data, add features, no disruption

---

## 📝 Development Guidelines

### Adding New Features

When adding features, consider deployment mode:

```python
@router.post("/v1/advanced-feature")
async def advanced_feature():
    """Advanced feature only available in platform mode."""
    config = get_config()
    
    if not config.features.is_platform_mode():
        raise HTTPException(
            status_code=403,
            detail="This feature requires Enterprise tier. Contact sales@dyocense.com"
        )
    
    # Platform-only implementation
    return {"result": "advanced"}
```

### Feature Visibility

**SMB Mode - Hide these in UI:**
- Evidence graph visualizations
- Vector search/semantic queries
- SSO/SAML configuration
- Advanced solver selection
- Custom data residency

**Platform Mode - Show everything**

---

## 🚦 Rollout Plan

### Week 1-2: SMB Launch
- Deploy SMB mode to production
- Pricing: Starter ($49), Growth ($199), Business ($499)
- Focus: Single-location small businesses
- Goal: 20 paying customers

### Month 2-3: SMB Optimization
- Collect feedback, improve onboarding
- Add SMB-specific features (industry templates)
- Build case studies
- Goal: $5K MRR

### Month 4-6: Platform Beta
- Deploy platform mode for select customers
- Pricing: Enterprise ($1999+)
- Focus: Multi-location, API access, enterprise needs
- Goal: 2-3 enterprise customers

### Month 7+: Dual-Path Operation
- Run both modes in production
- Clear upgrade path: Business → Enterprise
- Separate sales motions
- Goal: 50 SMB + 5 Enterprise customers

---

## 📞 Support

- **SMB Mode Issues:** support@dyocense.com
- **Platform Mode Issues:** enterprise@dyocense.com
- **Sales/Upgrades:** sales@dyocense.com

---

**Last Updated:** November 6, 2025  
**Owner:** Engineering Team  
**Status:** Active - SMB mode primary focus
