# Dyocense Stubs, Mocks & Fallbacks Documentation

This document catalogs all stub implementations, mock services, and fallback mechanisms in the Dyocense platform, documenting their purpose, behavior, and migration path to production implementations.

**Last Updated:** 5 November 2025  
**Status:** Development/In-Memory Mode

---

## Overview

The Dyocense platform is designed with graceful degradation patterns that allow local development and testing without external dependencies (MongoDB, Neo4j, Qdrant, Keycloak, LLM APIs). This document details each stub/fallback mechanism.

---

## 1. Authentication & Authorization

### 1.1 Demo Token Authentication
**File:** `packages/kernel_common/auth.py`

**Purpose:** Allow local development without Keycloak/OIDC setup.

**Behavior:**
```python
# Accepts tokens starting with "demo-" 
# Example: "Bearer demo-tenant" → tenant_id="demo-tenant", subject="stub-user"
if token.startswith("demo-"):
    return token, "stub-user"
```

**Production Path:**
- Replace with full OIDC/JWT validation
- Integrate with Keycloak for multi-realm tenant isolation
- Implement proper token expiry and refresh flows

**Test Coverage:** Used in 22 passing tests

---

### 1.2 Fallback Tenant (Demo Tenant)
**File:** `services/accounts/main.py:428`

**Purpose:** Provide demo tenant when database unavailable.

**Behavior:**
```python
# GET /v1/tenants/me returns synthetic tenant if DB lookup fails
tenant = Tenant(
    tenant_id=identity["tenant_id"],
    name="Demo Business",
    plan_tier=PlanTier.FREE,
    usage=TenantUsage(projects=0, playbooks=0, members=1, ...),
    api_token="demo-token"
)
```

**Production Path:**
- Enforce database requirement for tenant retrieval
- Remove fallback once deployment includes persistent MongoDB

---

### 1.3 Keycloak Fallback
**File:** `services/accounts/main.py`, `packages/trust/onboarding.py`

**Purpose:** Allow tenant registration when Keycloak unavailable.

**Behavior:**
- Tenant registration proceeds with warning log
- No temporary password issued; first user registers with tenant API token
- Status: `success_without_keycloak`

**Production Path:**
- Require Keycloak for production tenant onboarding
- Implement proper realm creation and SSO setup
- Enable MFA and external IdP integration

---

## 2. Data Persistence

### 2.1 InMemoryCollection
**File:** `packages/kernel_common/persistence.py`

**Purpose:** MongoDB fallback for local development.

**Behavior:**
- Mimics pymongo Collection API (insert_one, find_one, find, replace_one, delete_one)
- **Shared across services** in Kernel API (unified gateway)
- Data lost on process restart
- Collections cached by name in `_inmem_collections` dict

**API Coverage:**
```python
class InMemoryCollection:
    def insert_one(document: dict) -> None
    def find_one(query: dict) -> Optional[dict]
    def find(query: dict) -> Iterator[dict]
    def find_many(query: dict, limit: int) -> list[dict]
    def replace_one(query: dict, replacement: dict, upsert: bool) -> None
    def delete_one(query: dict) -> _DeleteResult
```

**Used By:**
- `accounts` (tenants, users, projects, API tokens, invitations)
- `versioning` (goal_versions ledger)
- `evidence` (run traces)

**Production Path:**
- Deploy MongoDB Atlas or self-hosted replica set
- Configure connection pooling and retry logic
- Implement backup/restore procedures
- Add indexes for query performance

**Test Coverage:** All 22 tests pass with in-memory collections

---

### 2.2 NullGraphStore (Neo4j Fallback)
**File:** `packages/kernel_common/graph.py`

**Purpose:** Disable Neo4j graph persistence in dev.

**Behavior:**
```python
class NullGraphStore:
    def ingest_evidence(self, record: dict) -> None:
        pass  # No-op
```

**Configuration:**
- Disabled by commenting `NEO4J_*` env vars in `.env`
- Fast-fail connection (max_retry_time=2.0s, connection_timeout=2.0s)
- Falls back immediately if connection refused

**Production Path:**
- Deploy Neo4j AuraDB or self-hosted cluster
- Implement evidence graph schema
- Build Cypher queries for lineage and impact analysis
- Enable real-time graph traversal APIs

---

### 2.3 InMemoryKnowledgeStore (Qdrant Fallback)
**File:** `packages/knowledge/store.py`

**Purpose:** Vector store fallback when Qdrant unavailable.

**Behavior:**
```python
class InMemoryKnowledgeStore(BaseKnowledgeStore):
    def search(self, query: str, limit: int) -> list[Document]:
        return []  # Returns empty results; no embeddings generated
```

**Production Path:**
- Deploy Qdrant Cloud or self-hosted instance
- Implement embedding generation (OpenAI/Azure embeddings)
- Ingest knowledge documents with metadata
- Build hybrid search (vector + keyword)

---

## 3. Compiler & LLM Services

### 3.1 Stub Compiler (LLM Fallback)
**File:** `services/compiler/main.py:188`

**Purpose:** Generate deterministic OPS when LLM unavailable.

**Behavior:**
```python
def _stub_ops(goal, tenant_id, project_id, data_inputs, artifacts):
    # Returns hardcoded inventory optimization problem
    # Uses demand/holding_cost from data_inputs if provided
    # Otherwise defaults: {"widget": 120, "gadget": 95}
    return {
        "objective": {"sense": "min", "expression": "..."},
        "decision_variables": [...],
        "parameters": {"demand": {...}, "holding_cost": {...}},
        "constraints": [...],
        "kpis": [...],
        "validation_notes": ["Generated via fallback compiler stub."]
    }
```

**Triggered When:**
- `azure-ai-openai` package not installed
- OpenAI API key missing/invalid
- LLM returns incomplete OPS (missing required sections)

**Production Path:**
- Install `azure-ai-inference` or `openai` SDK
- Configure LLM endpoints (Azure OpenAI or OpenAI API)
- Implement prompt engineering for OPS generation
- Add validation and retry logic
- Train/fine-tune models on OPS examples

**Test Coverage:** Compiler tests pass with stub

---

### 3.2 Base Metadata
**File:** `services/compiler/main.py:156`

**Purpose:** Provide minimal OPS metadata skeleton.

**Behavior:**
```python
def _base_metadata(goal, tenant_id, project_id):
    return {
        "metadata": {
            "ops_version": "1.0.0",
            "problem_type": "inventory_planning",
            "tenant_id": tenant_id,
            "project_id": project_id,
            "run_tags": ["goal", goal[:32]]
        }
    }
```

**Status:** Essential helper, not a stub (retains in production)

---

## 4. Optimization Services

### 4.1 Stub Solution (OR-Tools Fallback)
**File:** `services/optimiser/main.py:112`

**Purpose:** Deterministic solution when OR-Tools/Pyomo unavailable or fail.

**Behavior:**
```python
def _stub_solution(ops: dict) -> dict:
    # Extracts demand from OPS parameters
    # Returns deterministic stock assignments: stock[sku] = demand[sku] + 10
    # Calculates objective value from holding costs
    return {
        "status": "optimal",
        "objective_value": total_cost,
        "variables": {"stock": {...}},
        "solve_time_seconds": 0.001,
        "solver": "stub"
    }
```

**Triggered When:**
- OR-Tools solver fails (infeasibility, timeout, exception)
- Pyomo not installed or fails
- Constraint violations prevent solve

**Production Path:**
- Ensure OR-Tools/Pyomo installed and configured
- Add commercial solver backends (Gurobi, CPLEX) for complex problems
- Implement presolve diagnostics
- Add warm-start and solution polishing

**Test Coverage:** Optimiser tests exercise fallback path

---

## 5. Policy & Diagnostics Services

### 5.1 Policy Evaluation Stub
**File:** `services/policy/main.py:67`

**Purpose:** Placeholder policy checks.

**Behavior:**
```python
# Returns hardcoded policy results
{
    "checks": [
        {
            "policy": "inventory_sustainability",
            "status": "pass",
            "rationale": "Stock levels align with targets"
        },
        # ... more checks
    ],
    "overall_status": "pass"
}
```

**Production Path:**
- Implement policy rule engine (JSON rules or Python DSL)
- Integrate with external compliance systems
- Add configurable thresholds per tenant
- Build policy violation alerts

---

### 5.2 Diagnostician Stub
**File:** `services/diagnostician/main.py:35`

**Purpose:** Generate relaxation recommendations when infeasibility suspected.

**Behavior:**
```python
# Returns hardcoded relaxations
{
    "relaxations": [
        {
            "constraint": "demand_satisfaction",
            "type": "bound",
            "rationale": "Typical relaxation to absorb forecast volatility..."
        }
    ]
}
```

**Production Path:**
- Implement IIS (Irreducible Infeasible Subsystem) analysis
- Integrate solver diagnostics
- Build automated relaxation heuristics
- Add user-guided constraint tuning

---

### 5.3 Explainer Stub
**File:** `services/explainer/main.py:52`

**Purpose:** Template-based explanation generation.

**Behavior:**
```python
# Returns structured narrative with placeholders
{
    "summary": "Optimised inventory allocation...",
    "key_insights": ["Minimised holding costs...", ...],
    "recommendations": ["Consider increasing..."],
    "narrative": "The current stub emphasises inventory cost minimisation..."
}
```

**Production Path:**
- Integrate LLM for natural language generation
- Build domain-specific explanation templates
- Add visualization recommendations
- Implement "explain-by-example" scenarios

---

## 6. Marketplace & Catalog

### 6.1 Marketplace Catalog Stub
**File:** `services/marketplace/main.py:17`

**Purpose:** Expose template catalog without real OCI registry.

**Behavior:**
```python
# Returns hardcoded catalog from packages/archetypes/registry.json
# No actual package downloads or versioning
GET /v1/templates → {"items": [...], "count": N}
```

**Production Path:**
- Deploy OCI-compliant registry (Harbor, Azure Container Registry)
- Implement template versioning and publishing workflow
- Add template marketplace with ratings/reviews
- Build CI/CD for template validation and deployment

---

## 7. Evidence & Audit Trail

### 7.1 Evidence Dual-Write Pattern
**File:** `services/evidence/main.py:63`

**Purpose:** Ensure evidence captured even if MongoDB fails.

**Behavior:**
```python
try:
    collection.insert_one(record)  # MongoDB
except Exception:
    logger.warning("Mongo insert failed; storing in-memory fallback")
finally:
    fallback_collection.insert_one(sanitized)  # Always writes to in-memory
    graph_store.ingest_evidence(sanitized)  # Best-effort graph ingest
```

**Status:** Defensive pattern; keeps in production with monitoring

**Production Path:**
- Add event streaming (Kafka/Event Hubs) for reliable audit log
- Implement write-ahead logging
- Enable multi-region replication for evidence durability

---

## 8. UI Mocks & Simulations

### 8.1 AI Chat Simulation
**File:** `apps/ui/src/pages/PlaybookResultsPage.tsx`

**Purpose:** Simulated AI assistant for refining playbook parameters.

**Behavior:**
```typescript
const generateAIResponse = (userMessage: string): string => {
  const lower = userMessage.toLowerCase();
  if (lower.includes('horizon') || lower.includes('timeframe')) {
    return "I can adjust the planning horizon. Currently set to 6 months...";
  }
  // ... pattern matching for cost, demand, constraints
  return "I understand you want to refine the plan. Let me help...";
}
```

**Production Path:**
- Replace with real LLM API (OpenAI/Azure OpenAI)
- Implement parameter extraction and validation
- Build diff view for parameter changes
- Add chat history persistence

---

### 8.2 Goal Planner UI Stub & Persistence

**Files:**

- `apps/ui/src/lib/goalPlanner.ts`
- `apps/ui/src/lib/goalPlannerStore.ts`
- `apps/ui/src/pages/GoalPlannerPage.tsx`

**Purpose:** Enable Goal Planner experience without backend by providing:

- Deterministic client stub for analyze/refine
- Local-only versioning (save/restore) via `localStorage`
- Refinement history timeline with snapshot restore

**Behavior:**

```ts
// goalPlanner.ts
export function stubAnalyze(req: GoalRequest): GoalPlan { /* deterministic KPIs + actions */ }

export async function analyzeGoal(req: GoalRequest) {
    const fallback = stubAnalyze(req);
    const force = import.meta.env.VITE_GOAL_PLANNER_FORCE_STUB;
    if (force === '1' || force === 'true') return fallback;
    return fetchJSON('/v1/goal-planner/analyze', { method: 'POST', body: JSON.stringify(req), fallback });
}

export async function refineGoal(id: string, delta: PlanDelta) { /* same flag pattern */ }

// goalPlannerStore.ts (local versions)
export function savePlanSnapshot(plan: GoalPlan, req?: GoalRequest): SavedPlan { /* writes to localStorage */ }
export function listSavedPlans(): SavedPlan[];
export function deletePlan(id: string): void;
```

**UI Hooks:**

- Save version button saves current plan with metadata (goal, BU, markets, horizon)
- Versions panel lists local versions with Restore/Delete actions
- Refinement history shows each analyze/refine step; "View" restores that snapshot into the view

**Production Path:**

- Implement real endpoints per `docs/openapi/goal_planner.yaml`
- Replace local `SavedPlan` with server-side versioning (see `packages/versioning/`)
- Persist refinement events as a timeline (append-only ledger)
- Add optimistic UI with eventual consistency

---

## 9. Configuration & Feature Flags

### 9.1 Environment-Based Fallbacks

**Configuration Patterns:**

```bash
# .env
# NEO4J_URI=bolt://localhost:7687  # Commented = disabled
# MONGO_URI=mongodb://localhost:27017  # Missing = in-memory fallback
# ALLOW_ANONYMOUS=false  # Dev-only bypass
# UI: Force Goal Planner stub (skip network)
VITE_GOAL_PLANNER_FORCE_STUB=1
```

**Decision Logic:**
- Services attempt connection with short timeout
- On failure, fall back to in-memory/no-op implementation
- Log warnings for visibility but continue operation

---

## 10. Testing Strategy

### 10.1 Test Doubles Usage

**Pattern:**
- Tests use `TestClient` which instantiates services with in-memory backends
- No external dependencies required for test suite
- 22 tests pass with all fallbacks active

**Example:**
```python
def test_orchestrator_run_completes():
    client = TestClient(kernel_app)  # Uses in-memory collections
    headers = {"Authorization": "Bearer demo-tenant"}  # Demo token
    # ... test completes with stubs/fallbacks
```

---

## 11. Production Readiness Checklist

### Phase 1: Core Infrastructure
- [ ] Deploy MongoDB Atlas (or self-hosted replica set)
- [ ] Deploy Neo4j AuraDB (or self-hosted cluster)
- [ ] Deploy Qdrant Cloud (or self-hosted instance)
- [ ] Configure Keycloak with realms and clients

### Phase 2: LLM & AI Services
- [ ] Obtain Azure OpenAI or OpenAI API credentials
- [ ] Implement embedding generation pipeline
- [ ] Build prompt templates for compiler
- [ ] Add LLM monitoring and fallback policies

### Phase 3: Solver Infrastructure
- [ ] Validate OR-Tools/Pyomo on production hardware
- [ ] Evaluate commercial solver licenses (Gurobi, CPLEX)
- [ ] Implement solver timeout and resource limits
- [ ] Build solution quality validation

### Phase 4: Observability
- [ ] Replace stub/fallback warnings with metrics
- [ ] Add health checks for each external dependency
- [ ] Implement circuit breakers for degraded services
- [ ] Build dashboard for stub activation rates

### Phase 5: Security & Compliance
- [ ] Remove demo token authentication
- [ ] Enforce OIDC/JWT validation
- [ ] Implement API rate limiting
- [ ] Add audit logging for evidence writes
- [ ] Enable encryption at rest and in transit

---

## 12. Migration Scripts

### 12.1 Data Migration from In-Memory to MongoDB

**Scenario:** Transitioning from development to staging/production.

**Strategy:**
```python
# Export in-memory data (add to services before restart)
import json
from packages.kernel_common.persistence import _inmem_collections

def export_inmem_data(output_dir: str):
    for name, coll in _inmem_collections.items():
        data = list(coll._documents)
        with open(f"{output_dir}/{name}.json", "w") as f:
            json.dump(data, f, indent=2, default=str)

# Import to MongoDB (run once after MongoDB deployment)
def import_to_mongo(input_dir: str):
    from pymongo import MongoClient
    client = MongoClient(os.getenv("MONGO_URI"))
    db = client[os.getenv("MONGO_DB_NAME")]
    
    for file_path in Path(input_dir).glob("*.json"):
        coll_name = file_path.stem
        with open(file_path) as f:
            documents = json.load(f)
        if documents:
            db[coll_name].insert_many(documents)
```

---

## 13. Stub Removal Timeline

**Recommended Phasing:**

| Phase | Component | Priority | Effort |
|-------|-----------|----------|--------|
| 1 | MongoDB (replace InMemoryCollection) | Critical | Low |
| 1 | Keycloak (replace demo tokens) | High | Medium |
| 2 | LLM Compiler (replace stub OPS) | High | Medium |
| 2 | Neo4j (replace NullGraphStore) | Medium | Medium |
| 3 | Qdrant (replace InMemoryKnowledgeStore) | Medium | Low |
| 3 | Policy Engine (replace stub checks) | Low | High |
| 4 | Advanced Solvers (commercial licenses) | Low | High |
| 4 | AI Chat (replace simulation) | Low | Medium |

---

## 14. Monitoring & Alerts

### 14.1 Recommended Metrics

**Stub Activation Rate:**
```python
# Add to each fallback path
metrics.counter("fallback.activated", tags=["component:persistence", "reason:mongo_down"])
```

**Key Metrics:**
- `fallback.inmemory.collections` - Number of collections using in-memory mode
- `fallback.compiler.stub_ops` - Count of stub compiler invocations
- `fallback.solver.stub_solution` - Count of deterministic solver fallbacks
- `auth.demo_token.usage` - Demo token authentication count (should be 0 in prod)

**Alert Thresholds (Production):**
- ANY stub activation → Page on-call
- Demo token usage > 0 → Critical alert
- Fallback rate > 1% → Warning

---

## 15. Developer Guidelines

### 15.1 Adding New Stubs

**When to Use Stubs:**
- External service not available in dev environment
- Complex setup required for local testing
- Cost/licensing constraints for development

**Pattern:**
```python
try:
    # Attempt real implementation
    result = real_service.call()
except ServiceUnavailableError:
    logger.warning("Service unavailable; using stub")
    result = stub_implementation()
```

### 15.2 Documentation Requirements

**For Each Stub:**
1. Docstring explaining stub purpose
2. Comment linking to production implementation ticket
3. Test coverage demonstrating stub behavior
4. Migration guide in this document

---

## 16. FAQ

**Q: Why so many stubs/fallbacks?**  
A: Enables zero-dependency local development and testing. Developers can run the full stack without Docker, cloud services, or API keys.

**Q: Are stubs tested?**  
A: Yes. All 22 tests pass using stubs/fallbacks. Integration tests will validate production implementations.

**Q: How do I disable fallbacks in production?**  
A: Set environment variables for real services. Add health checks that fail if fallbacks activate. Use feature flags to enforce strict mode.

**Q: What happens if MongoDB fails in production?**  
A: Evidence service writes to in-memory fallback as backup. Add monitoring to alert on this condition. Consider event streaming for durability.

**Q: Can I mix stub and real implementations?**  
A: Yes. Each component fails over independently. You can run with MongoDB + stub compiler, for example.

---

## 17. Summary Statistics

**Current State (Development Mode):**
- **Total Stub Components:** 15
- **Critical Dependencies Stubbed:** 4 (MongoDB, Neo4j, Qdrant, Keycloak)
- **Service-Level Fallbacks:** 8 (Compiler, Solver, Policy, Diagnostician, Explainer, Evidence, Auth, Knowledge)
- **Test Pass Rate:** 100% (22/22 tests)
- **In-Memory Collections Active:** 9 (tenants, users, projects, tokens, invitations, goal_versions, evidence, etc.)

**Lines of Stub Code:** ~500 LOC across all components  
**Production Readiness:** ~60% (core logic complete, external dependencies stubbed)

---

## 18. Contact & Ownership

**Document Owner:** Engineering Team  
**Last Review:** 5 November 2025  
**Next Review:** Before production deployment

**Questions?** Refer to:
- Architecture docs: `docs/docs/architecture.md`
- API specs: `docs/openapi/openapi.yaml`
- Component READMEs in each `services/*/README.md`
