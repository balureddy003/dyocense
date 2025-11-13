# Coach V4 Implementation Phases (P0–P2)

This plan tracks incremental delivery with minimal disruption while unlocking unique SMB value.

## Phase Plan

### Phase 0 (P0): Infrastructure & Flags

**Status:** Complete
**Timeline:** Shipped
**Goal:** Flag-gated infrastructure for adaptive features

### Phase 1 (P1): Metabolism & Pacing

**Status:** Complete
**Timeline:** 12 Nov 2025
**Goal:** Adaptive pacing based on business health and workload

**Delivered Features:**

- **Metabolism Model**: Heuristic fitness energy model with capacity estimation
  - Energy capacity (0-100) based on health score
  - Fatigue and recovery rate calculations
  - Projected weekly task capacity
  - Risk flags for overload conditions
- **Pacing Integration**: Task generation respects metabolic capacity
  - Caps new tasks based on available capacity
  - Prevents user overload
  - Maintains minimum task generation (floor of 1)
- **Coach Context Enhancement**: Metabolism data in business context
  - Coach can adapt recommendations based on capacity
  - Pacing-aware suggestions
- **Decision Ledger Verification**: Admin-only integrity checks
  - HMAC signature verification
  - Basic parent linkage validation
  - Guarded by `ADMIN_ENABLE_LEDGER_VERIFY` flag

**API Changes:**

- New endpoint: `GET /v1/tenants/{tenant_id}/ledger/verify` (admin-guarded)
- Enhanced: `POST /v1/tenants/{tenant_id}/goals/{goal_id}/generate-tasks` (pacing)
- Enhanced: `POST /v1/tenants/{tenant_id}/coach/chat` (metabolism in context)

**Documentation:**

- See `docs/PHASE1_METABOLISM_PACING_LOG.md` for detailed implementation log

## P1 (in-progress)

- Adaptive Health Score extensions
  - Data Quality Index, optional CI bounds (flag-gated)
  - Optional ADWIN drift flags (river, best-effort)
- Decision Ledger (Phase-1)
  - Append-only Postgres table, HMAC signatures, chain by parent id
  - Endpoints: commit, chain
  - Instrument key endpoints (task create/update, tasks from goal, health score record)
- Goal Metabolism (Phase-1)
  - Heuristic energy/fatigue/recovery model and `/metabolism/preview`
- Security checklist and env hygiene docs

## P2 (Adaptive Coach & Integrity)

**Status:** Complete
**Timeline:** 12 Nov 2025
**Goal:** Adaptive coaching with historical context and ledger integrity monitoring

**Delivered Features:**

- **Coach Feedback Loop**: Automatic interaction logging
  - Coach interactions logged to decision ledger with pre/post state
  - Historical health score trends extracted and provided to coach
  - Adaptive recommendations based on score trajectory
- **Health Score Trend Tracking**: Historical context for coaching
  - `_get_health_score_trend()` extracts deltas from ledger
  - Trend direction classification (improving/declining/stable)
  - Integrated into coach business context
- **Metabolism Recovery Suggestions**: Fatigue-aware recommendations
  - High fatigue (>0.7): Explicit recovery window (3-5 days)
  - Moderate fatigue (>0.5): Lighter workload suggestions
  - Enhanced basis with fatigue level and effective energy
- **Ledger Integrity Summary**: Lightweight monitoring endpoint
  - `GET /ledger/integrity`: Stats without full entry details
  - Action type distribution and entry counts
  - Fast health checks for dashboards (<100ms)

**API Changes:**

- New endpoint: `GET /v1/tenants/{tenant_id}/ledger/integrity` (public, fast summary)
- Enhanced: `POST /v1/tenants/{tenant_id}/coach/chat` (logs to ledger, includes trend)
- Enhanced: Metabolism model (recovery suggestions in risks array)

**Documentation:**

- See `docs/PHASE2_ADAPTIVE_COACH_LOG.md` for detailed implementation log

## P3 (future)

- Move signatures to per-tenant asymmetric keys
- Optional micro-seasonality (statsmodels) under feature flag
- Secret management: Move sensitive envs to a managed secret store per environment
- Coach learning loop: Track recommendation outcomes and effectiveness
- Automated background integrity verification jobs

## Flags & defaults

- `ENABLE_ADAPTIVE_HEALTH`: gates CI and drift detection; on in dev only
- river optional dependency: no-op if not installed

## Risk & rollback

- All P1 features are additive and behind safe defaults; removing new endpoints or toggling flags reverts behavior.
