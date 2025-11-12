from __future__ import annotations

import uuid
from importlib import resources
import json
import os
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
import jsonschema

# PostgreSQL persistence layer
from packages.kernel_common.logging import configure_logging
from packages.kernel_common.persistence_v2 import get_backend

logger = configure_logging("smb-gateway")

from .health_score import HealthScoreCalculator, HealthScoreResponse
from .goals_service import (
    get_goals_service,
    CreateGoalRequest,
    UpdateGoalRequest,
    Goal,
    GoalStatus,
)
from .tasks_service import (
    get_tasks_service,
    CreateTaskRequest,
    UpdateTaskRequest,
    Task,
    TaskStatus,
    TaskHorizon,
)
from .coach_service import (
    get_coach_service,
    ChatRequest,
    ChatResponse,
    ChatMessage,
)
from .coach_personas import PersonaConfig, CoachPersona
from .conversational_coach import (
    get_conversational_coach,
)
from .multi_agent_coach import (
    get_multi_agent_coach,
)
from .report_generator import (
    get_report_generator,
    ReportFormat,
    AgentThought,
    Evidence,
    ReportSection,
)
from .run_logs import (
    create_run as create_runlog,
    append_event as runlog_append_event,
    append_output as runlog_append_output,
    finalize_run as runlog_finalize,
    list_runs as runlog_list,
    get_run as runlog_get,
)
from .analytics_service import (
    get_analytics_service,
    HealthScoreHistoryPoint,
    GoalProgressPoint,
    TaskCompletionStats,
    CategoryBreakdown,
)
from .achievements_service import (
    get_achievements_service,
    Achievement,
    AchievementProgress,
)
from .settings_service import (
    get_settings_service,
    TenantSettings,
    NotificationSettings,
    AccountSettings,
    AppearanceSettings,
    IntegrationSettings,
)

# Load shared schemas
plan_schema = json.loads(resources.files("packages.contracts.schemas").joinpath("plan.schema.json").read_text(encoding="utf-8"))
workspace_schema = json.loads(resources.files("packages.contracts.schemas").joinpath("workspace.schema.json").read_text(encoding="utf-8"))

# Initialize PostgreSQL backend
db_backend = get_backend()
if not db_backend.connect():
    logger.warning("Failed to connect to PostgreSQL. Some features may not work.")


def _sample_plan(title: str) -> Dict:
    return {
        "id": f"plan-{uuid.uuid4().hex[:8]}",
        "title": title,
        "summary": "Dyocense generated getting-started plan.",
        "created_at": "",
        "updated_at": "",
        "tasks": [
            {"label": "Define MVP scope", "owner": "Founder", "status": "In progress"},
            {"label": "Assign owners", "owner": "Ops lead", "status": "Not started"},
            {"label": "Launch pilot", "owner": "CX lead", "status": "Not started"},
        ],
    }


def _sample_workspace(name: str) -> Dict:
    return {
        "id": f"ws-{uuid.uuid4().hex[:8]}",
        "name": name,
        "industry": "general_smb",
        "region": "na",
        "created_at": "",
        "updated_at": "",
    }


TENANT_PLANS: Dict[str, List[Dict]] = {}
TENANT_WORKSPACES: Dict[str, Dict] = {}
TENANT_CONNECTOR_DATA: Dict[str, Dict] = {}  # Mock connector data storage


class OnboardingRequest(BaseModel):
    workspace_name: str = Field(default="Sample Workspace")
    plan_title: str = Field(default="Sample Launch Plan")
    archetype_id: str | None = Field(default=None, description="Template used to seed the plan.")


app = FastAPI(
    title="SMB Gateway",
    version="0.1.0",
    description="Stubbed onboarding + plan endpoints consumed by the SMB UI.",
)


def _store_plan(tenant_id: str, plan: Dict) -> None:
    TENANT_PLANS.setdefault(tenant_id, [])
    existing = TENANT_PLANS[tenant_id]
    # Keep latest at front
    existing.insert(0, plan)
    TENANT_PLANS[tenant_id] = existing[:10]


@app.post("/v1/onboarding/{tenant_id}")
def run_onboarding(tenant_id: str, body: OnboardingRequest):
    workspace = _sample_workspace(body.workspace_name)
    plan = _sample_plan(body.plan_title)

    try:
        jsonschema.validate(instance=workspace, schema=workspace_schema)
        jsonschema.validate(instance=plan, schema=plan_schema)
    except jsonschema.ValidationError as exc:
        raise HTTPException(status_code=500, detail=f"Schema validation failed: {exc.message}") from exc

    TENANT_WORKSPACES[tenant_id] = workspace
    _store_plan(tenant_id, plan)

    return {"workspace": workspace, "plan": plan}


@app.get("/v1/tenants/{tenant_id}/plans")
def list_plans(tenant_id: str, limit: int = Query(default=5, ge=1, le=20)):
    items = TENANT_PLANS.get(tenant_id)
    if not items:
        # generate default sample if onboarding not run
        plan = _sample_plan("Sample Launch Plan")
        jsonschema.validate(instance=plan, schema=plan_schema)
        TENANT_PLANS[tenant_id] = [plan]
        items = TENANT_PLANS[tenant_id]
    return {"items": items[:limit], "count": len(items)}


class PlanCreateRequest(BaseModel):
    goal_id: Optional[str] = None
    archetype_id: Optional[str] = Field(default="forecasting_basic", description="Template/archetype ID")
    regenerate: bool = Field(default=False, description="Force regeneration even if plan exists")


@app.post("/v1/tenants/{tenant_id}/plans")
async def create_plan(tenant_id: str, request: PlanCreateRequest):
    """
    Create or regenerate an action plan for the tenant.
    Links to goal if goal_id provided; calls planner service for structured execution.
    """
    # Build plan goal/title from linked goal if available
    goals_service = get_goals_service()
    plan_title = "Action Plan"
    goal_context = None
    
    if request.goal_id:
        try:
            goal_obj = goals_service.get_goal(tenant_id, request.goal_id)
            if goal_obj:
                plan_title = f"Action Plan: {goal_obj.title}"
                goal_context = {
                    "goal_id": goal_obj.id,
                    "title": goal_obj.title,
                    "category": goal_obj.category,
                    "target": goal_obj.target,
                    "current": goal_obj.current,
                }
        except Exception:
            pass  # proceed without goal context
    
    # Generate a structured plan via the planner service (optional integration)
    # For MVP, create a sample plan and store it
    plan = _sample_plan(plan_title)
    
    # Enrich with goal linkage and metadata
    plan["goal_id"] = request.goal_id
    plan["archetype_id"] = request.archetype_id
    plan["created_at"] = datetime.now().isoformat()
    plan["tenant_id"] = tenant_id
    
    # Validate and store
    jsonschema.validate(instance=plan, schema=plan_schema)
    _store_plan(tenant_id, plan)
    
    return plan


@app.get("/v1/tenants/{tenant_id}/health-score", response_model=HealthScoreResponse)
async def get_health_score(tenant_id: str):
    """
    Calculate business health score from connector data
    
    Returns health score (0-100) with breakdown by category:
    - Revenue health (growth, sales velocity)
    - Operations health (inventory turnover, stockouts)
    - Customer health (repeat rate, retention)
    """
    # Fetch connector data for this tenant
    # TODO: Replace with actual connector service call
    connector_data = await _fetch_connector_data(tenant_id)
    
    # Calculate health score
    calculator = HealthScoreCalculator(connector_data)
    health_score = calculator.calculate_overall_health()
    
    return health_score


async def _fetch_connector_data(tenant_id: str) -> Dict:
    """
    Fetch connector data for a tenant.
    
    Strategy:
    1. Check in-memory mock data first (for development/testing)
    2. Query connectors API to check for active connectors
    3. If connectors exist with synced data, fetch from connector_data table
    4. Otherwise return empty structure
    
    Returns dict with orders, inventory, customers arrays.
    """
    # Check in-memory mock data first (for development/testing)
    if tenant_id in TENANT_CONNECTOR_DATA:
        logger.info(f"[_fetch_connector_data] Using in-memory data for tenant {tenant_id}")
        return TENANT_CONNECTOR_DATA[tenant_id]
    
    # Use connectors repository to check for active connectors
    try:
        from packages.connectors.repository_postgres import ConnectorRepositoryPG
        from packages.connectors.models import ConnectorStatus
        from packages.kernel_common.persistence_v2 import get_backend, PostgresBackend
        
        logger.info(f"[_fetch_connector_data] Checking connectors for tenant {tenant_id}")
        
        connector_repo = ConnectorRepositoryPG()
        connectors = connector_repo.list_by_tenant(tenant_id, status=ConnectorStatus.ACTIVE)
        
        if not connectors:
            logger.info(f"[_fetch_connector_data] No active connectors for tenant {tenant_id}")
            return {
                "orders": [],
                "inventory": [],
                "customers": [],
                "has_data_connected": False,
                "_meta": {
                    "fetched_at": datetime.now().isoformat(),
                    "tenant_id": tenant_id,
                    "data_source": "connectors_api",
                    "note": "No active connectors found. Add and activate a connector to import data."
                }
            }
        
        logger.info(f"[_fetch_connector_data] Found {len(connectors)} active connectors for tenant {tenant_id}")
        
        # Query connector_data (compact) + connector_data_chunks (chunked) with single tenant-scoped queries
        try:
            backend = get_backend()
            if not isinstance(backend, PostgresBackend):
                raise RuntimeError("PostgresBackend required for connector data queries")

            result = {
                "orders": [],
                "inventory": [],
                "customers": [],
                "products": [],
                "has_data_connected": True,
                "metadata": {
                    "is_sample_data": False,
                    "orders_source": None,
                    "inventory_source": None,
                    "customers_source": None,
                    "active_connectors": len(connectors),
                    "connector_names": {c.connector_id: c.display_name for c in connectors},
                },
                "_meta": {
                    "fetched_at": datetime.now().isoformat(),
                    "tenant_id": tenant_id,
                    "data_source": "connector_data_table+chunks",
                    "active_connectors": len(connectors),
                    "connector_types": [c.connector_type for c in connectors],
                }
            }

            connector_ids = [c.connector_id for c in connectors]
            data_source_map = {}  # Track which connector provided which data type

            with backend.get_connection() as conn:
                with conn.cursor() as cur:
                    # Compact rows in one query
                    cur.execute(
                        """
                        SELECT connector_id, data_type, data, record_count, synced_at
                        FROM connectors.connector_data
                        WHERE tenant_id = %s AND connector_id = ANY(%s)
                        ORDER BY synced_at DESC
                        """,
                        (tenant_id, connector_ids)
                    )
                    compact_rows = cur.fetchall()
                    for connector_id, data_type, data_array, record_count, _ in compact_rows:
                        if data_type in result:
                            if isinstance(data_array, list):
                                result[data_type].extend(data_array)
                            else:
                                result[data_type].append(data_array)
                            logger.debug(f"[_fetch_connector_data] Merged {record_count} {data_type} (compact)")
                            
                            # Track data source
                            if data_type not in data_source_map:
                                connector_name = result["metadata"]["connector_names"].get(connector_id, connector_id)
                                data_source_map[data_type] = f"{connector_name} ({record_count} records)"

                    # Chunked rows in one query (ordered by latest first, chunk order descending)
                    try:
                        cur.execute(
                            """
                            SELECT connector_id, data_type, data, record_count, synced_at
                            FROM connectors.connector_data_chunks
                            WHERE tenant_id = %s AND connector_id = ANY(%s)
                            ORDER BY synced_at DESC, chunk_index DESC
                            """,
                            (tenant_id, connector_ids)
                        )
                        chunk_rows = cur.fetchall()
                        for connector_id, data_type, data_array, record_count, _ in chunk_rows:
                            if data_type in result:
                                if isinstance(data_array, list):
                                    result[data_type].extend(data_array)
                                else:
                                    result[data_type].append(data_array)
                                logger.debug(f"[_fetch_connector_data] Merged {record_count} {data_type} (chunk)")
                                
                                # Track data source if not already tracked
                                if data_type not in data_source_map:
                                    connector_name = result["metadata"]["connector_names"].get(connector_id, connector_id)
                                    data_source_map[data_type] = f"{connector_name} ({record_count} records)"
                    except Exception as e:
                        # Graceful degradation when chunks table not yet migrated
                        logger.warning("[_fetch_connector_data] Skipping chunks: %s", str(e))
            
            # Populate metadata with data sources
            result["metadata"]["orders_source"] = data_source_map.get("orders")
            result["metadata"]["inventory_source"] = data_source_map.get("inventory")
            result["metadata"]["customers_source"] = data_source_map.get("customers")

            total_records = (
                len(result.get("orders", [])) +
                len(result.get("inventory", [])) +
                len(result.get("customers", [])) +
                len(result.get("products", []))
            )

            logger.info(
                f"[_fetch_connector_data] Aggregated records for tenant {tenant_id}: "
                f"orders={len(result['orders'])} inventory={len(result['inventory'])} "
                f"customers={len(result['customers'])} products={len(result['products'])} total={total_records}"
            )

            result["_meta"]["total_records"] = total_records
            result["_meta"]["note"] = (
                "Connectors configured but no data synced yet. Upload CSV or sync connector data." if total_records == 0
                else f"Loaded {total_records} total records from {len(connectors)} active connectors"
            )
            return result
            
        except Exception as db_error:
            logger.error(f"[_fetch_connector_data] Database query failed: {db_error}")
            import traceback
            traceback.print_exc()
            
            # Fallback to empty arrays if DB query fails
            return {
                "orders": [],
                "inventory": [],
                "customers": [],
                "has_data_connected": True,
                "_meta": {
                    "fetched_at": datetime.now().isoformat(),
                    "tenant_id": tenant_id,
                    "data_source": "connectors_api",
                    "active_connectors": len(connectors),
                    "connector_types": [c.connector_type for c in connectors],
                    "note": f"Connectors configured but failed to query data: {str(db_error)}"
                }
            }
    
    except Exception as e:
        logger.error(f"[_fetch_connector_data] Failed to fetch connector data for tenant {tenant_id}: {e}")
        import traceback
        traceback.print_exc()
        return {
            "orders": [],
            "inventory": [],
            "customers": [],
            "has_data_connected": False,
            "_meta": {
                "fetched_at": datetime.now().isoformat(),
                "tenant_id": tenant_id,
                "data_source": "error",
                "note": f"Error fetching connector data: {str(e)}"
            }
        }


# ===================================
# Business Profile & Onboarding Endpoints
# ===================================

class BusinessProfileRequest(BaseModel):
    """Business profile data from welcome wizard"""
    industry: Optional[str] = None
    company_size: Optional[str] = None
    team_size: Optional[str] = None
    primary_goal: Optional[str] = None
    business_type: Optional[str] = None
    additional_info: Optional[Dict[str, Any]] = None


class OnboardingCompleteRequest(BaseModel):
    """Complete onboarding with welcome wizard selections"""
    health_score: Optional[int] = None
    selected_goal: Optional[Dict[str, Any]] = None
    business_profile: Optional[Dict[str, Any]] = None


@app.post("/v1/tenants/{tenant_id}/profile/business")
async def update_business_profile(tenant_id: str, profile: BusinessProfileRequest):
    """
    Save or update business profile for tenant.
    Updates tenant metadata in PostgreSQL with profile information.
    """
    try:
        import psycopg2
        from psycopg2.extras import RealDictCursor, Json
        import os
        
        pg_url = os.getenv("POSTGRES_URL")
        if not pg_url:
            # Build connection string
            pg_host = os.getenv("POSTGRES_HOST", "localhost")
            pg_port = os.getenv("POSTGRES_PORT", "5432")
            pg_db = os.getenv("POSTGRES_DB", "dyocense")
            pg_user = os.getenv("POSTGRES_USER", "dyocense")
            pg_pass = os.getenv("POSTGRES_PASSWORD", "pass@1234")
            pg_url = f"postgresql://{pg_user}:{pg_pass}@{pg_host}:{pg_port}/{pg_db}"
        
        conn = psycopg2.connect(pg_url, cursor_factory=RealDictCursor)
        try:
            with conn.cursor() as cur:
                # Build profile dict
                profile_data = {
                    "industry": profile.industry,
                    "company_size": profile.company_size,
                    "team_size": profile.team_size,
                    "primary_goal": profile.primary_goal,
                    "business_type": profile.business_type,
                    "profile_updated_at": datetime.utcnow().isoformat(),
                }
                
                # Add additional info if provided
                if profile.additional_info:
                    profile_data.update(profile.additional_info)
                
                # Update tenant metadata
                cur.execute("""
                    UPDATE tenants.tenants
                    SET metadata = COALESCE(metadata, '{}'::jsonb) || %s::jsonb,
                        updated_at = NOW()
                    WHERE tenant_id = %s
                    RETURNING tenant_id
                """, (Json(profile_data), tenant_id))
                
                result = cur.fetchone()
                conn.commit()
                
                if not result:
                    raise HTTPException(status_code=404, detail=f"Tenant {tenant_id} not found")
                
                logger.info(f"Updated business profile for tenant {tenant_id}")
                
                return {
                    "success": True,
                    "message": "Business profile updated successfully",
                    "profile": profile_data
                }
        finally:
            conn.close()
            
    except psycopg2.Error as e:
        logger.error(f"Database error updating profile for {tenant_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    except Exception as e:
        logger.error(f"Error updating profile for {tenant_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/v1/tenants/{tenant_id}/onboarding/complete")
async def complete_onboarding(tenant_id: str, request: OnboardingCompleteRequest):
    """
    Mark onboarding as complete and save welcome wizard selections.
    
    Saves:
    - Health score baseline
    - Selected goal (creates goal if provided)
    - Business profile
    - Onboarding completion timestamp
    """
    try:
        import psycopg2
        from psycopg2.extras import RealDictCursor, Json
        import os
        
        pg_url = os.getenv("POSTGRES_URL")
        if not pg_url:
            pg_host = os.getenv("POSTGRES_HOST", "localhost")
            pg_port = os.getenv("POSTGRES_PORT", "5432")
            pg_db = os.getenv("POSTGRES_DB", "dyocense")
            pg_user = os.getenv("POSTGRES_USER", "dyocense")
            pg_pass = os.getenv("POSTGRES_PASSWORD", "pass@1234")
            pg_url = f"postgresql://{pg_user}:{pg_pass}@{pg_host}:{pg_port}/{pg_db}"
        
        conn = psycopg2.connect(pg_url, cursor_factory=RealDictCursor)
        try:
            with conn.cursor() as cur:
                # Build onboarding metadata
                onboarding_data = {
                    "onboarding_completed": True,
                    "onboarding_completed_at": datetime.utcnow().isoformat(),
                    "initial_health_score": request.health_score,
                }
                
                # Add business profile if provided
                if request.business_profile:
                    onboarding_data.update(request.business_profile)
                
                # Update tenant metadata
                cur.execute("""
                    UPDATE tenants.tenants
                    SET metadata = COALESCE(metadata, '{}'::jsonb) || %s::jsonb,
                        updated_at = NOW()
                    WHERE tenant_id = %s
                    RETURNING tenant_id
                """, (Json(onboarding_data), tenant_id))
                
                result = cur.fetchone()
                if not result:
                    conn.rollback()
                    raise HTTPException(status_code=404, detail=f"Tenant {tenant_id} not found")
                
                conn.commit()
                
                # Create goal if provided
                goal_id = None
                if request.selected_goal:
                    try:
                        goals_service = get_goals_service()
                        goal_request = CreateGoalRequest(
                            title=request.selected_goal.get('title', 'Business Goal'),
                            description=request.selected_goal.get('description', ''),
                            current=request.selected_goal.get('current', 0.0),
                            target=request.selected_goal.get('target', 100.0),
                            unit=request.selected_goal.get('unit', 'units'),
                            deadline=request.selected_goal.get('deadline', (datetime.utcnow() + timedelta(days=90)).strftime('%Y-%m-%d')),
                            category=request.selected_goal.get('category', 'revenue'),
                        )
                        goal = goals_service.create_goal(tenant_id, goal_request)
                        goal_id = goal.id
                        logger.info(f"Created onboarding goal {goal_id} for tenant {tenant_id}")
                    except Exception as e:
                        logger.warning(f"Failed to create onboarding goal: {e}")
                
                logger.info(f"Completed onboarding for tenant {tenant_id}")
                
                return {
                    "success": True,
                    "message": "Onboarding completed successfully",
                    "goal_id": goal_id,
                    "tenant_id": tenant_id
                }
        finally:
            conn.close()
            
    except psycopg2.Error as e:
        logger.error(f"Database error completing onboarding for {tenant_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    except Exception as e:
        logger.error(f"Error completing onboarding for {tenant_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ===================================
# Goals Endpoints
# ===================================

@app.post("/v1/tenants/{tenant_id}/goals", response_model=Goal)
async def create_goal(tenant_id: str, request: CreateGoalRequest):
    """Create a new goal for the tenant"""
    goals_service = get_goals_service()
    
    try:
        goal = goals_service.create_goal(tenant_id, request)
        return goal
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/v1/tenants/{tenant_id}/goals", response_model=List[Goal])
async def get_goals(tenant_id: str, status: Optional[GoalStatus] = Query(None)):
    """Get all goals for the tenant"""
    goals_service = get_goals_service()
    goals = goals_service.get_goals(tenant_id, status=status)
    return goals


@app.get("/v1/tenants/{tenant_id}/goals/{goal_id}", response_model=Goal)
async def get_goal(tenant_id: str, goal_id: str):
    """Get a specific goal"""
    goals_service = get_goals_service()
    goal = goals_service.get_goal(tenant_id, goal_id)
    
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")
    
    return goal


@app.put("/v1/tenants/{tenant_id}/goals/{goal_id}", response_model=Goal)
async def update_goal(tenant_id: str, goal_id: str, request: UpdateGoalRequest):
    """Update a goal"""
    goals_service = get_goals_service()
    goal = goals_service.update_goal(tenant_id, goal_id, request)
    
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")
    
    return goal


@app.delete("/v1/tenants/{tenant_id}/goals/{goal_id}")
async def delete_goal(tenant_id: str, goal_id: str):
    """Delete a goal"""
    goals_service = get_goals_service()
    success = goals_service.delete_goal(tenant_id, goal_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Goal not found")
    
    return {"message": "Goal deleted successfully"}


@app.post("/v1/tenants/{tenant_id}/goals/sync")
async def sync_auto_tracked_goals(tenant_id: str):
    """Sync auto-tracked goals with connector data"""
    goals_service = get_goals_service()
    
    # Fetch connector data
    connector_data = await _fetch_connector_data(tenant_id)
    
    # Update auto-tracked goals
    updated_goals = await goals_service.update_auto_tracked_goals(tenant_id, connector_data)
    
    return {
        "message": f"Synced {len(updated_goals)} auto-tracked goals",
        "updated_goals": updated_goals
    }


# ===================================
# Tasks Endpoints
# ===================================

@app.post("/v1/tenants/{tenant_id}/tasks", response_model=Task)
async def create_task(tenant_id: str, request: CreateTaskRequest):
    """Create a new task for the tenant"""
    tasks_service = get_tasks_service()
    
    try:
        task = tasks_service.create_task(tenant_id, request)
        return task
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/v1/tenants/{tenant_id}/tasks", response_model=List[Task])
async def get_tasks(
    tenant_id: str,
    status: Optional[TaskStatus] = Query(None),
    horizon: Optional[TaskHorizon] = Query(None),
    goal_id: Optional[str] = Query(None),
    limit: Optional[int] = Query(None),
):
    """Get all tasks for the tenant with optional filters"""
    tasks_service = get_tasks_service()
    tasks = tasks_service.get_tasks(tenant_id, status=status, horizon=horizon, goal_id=goal_id, limit=limit)
    return tasks


@app.get("/v1/tenants/{tenant_id}/tasks/{task_id}", response_model=Task)
async def get_task(tenant_id: str, task_id: str):
    """Get a specific task"""
    tasks_service = get_tasks_service()
    task = tasks_service.get_task(tenant_id, task_id)
    
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    return task


@app.put("/v1/tenants/{tenant_id}/tasks/{task_id}", response_model=Task)
async def update_task(tenant_id: str, task_id: str, request: UpdateTaskRequest):
    """Update a task"""
    tasks_service = get_tasks_service()
    task = tasks_service.update_task(tenant_id, task_id, request)
    
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    return task


@app.delete("/v1/tenants/{tenant_id}/tasks/{task_id}")
async def delete_task(tenant_id: str, task_id: str):
    """Delete a task"""
    tasks_service = get_tasks_service()
    success = tasks_service.delete_task(tenant_id, task_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Task not found")
    
    return {"message": "Task deleted successfully"}


@app.post("/v1/tenants/{tenant_id}/goals/{goal_id}/generate-tasks")
async def generate_tasks_from_goal(tenant_id: str, goal_id: str):
    """Generate AI-powered tasks from a goal"""
    tasks_service = get_tasks_service()
    goals_service = get_goals_service()
    
    # Get the goal
    goal = goals_service.get_goal(tenant_id, goal_id)
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")
    
    # Generate tasks
    goal_data = goal.dict()
    generated_tasks = tasks_service.generate_tasks_from_goal(tenant_id, goal_data)
    
    return {
        "message": f"Generated {len(generated_tasks)} tasks for goal",
        "tasks": generated_tasks
    }


# ===================================
# AI Coach Endpoints
# ===================================

@app.get("/v1/tenants/{tenant_id}/data-source")
async def get_data_source_info(tenant_id: str):
    """Get information about connected data sources"""
    # Fetch connector data
    connector_data = await _fetch_connector_data(tenant_id)
    
    # Check if has real data from database (not in-memory mock)
    has_real_data = connector_data.get("has_data_connected", False)
    
    # Count records
    total_orders = len(connector_data.get("orders", []))
    total_inventory = len(connector_data.get("inventory", []))
    total_customers = len(connector_data.get("customers", []))
    
    return {
        "orders": total_orders,
        "inventory": total_inventory,
        "customers": total_customers,
        "hasRealData": has_real_data,
        "connectedSources": [] if not has_real_data else ["shopify"],  # Example
        "lastSyncedAt": connector_data.get("_meta", {}).get("generated") if not has_real_data else None
    }

@app.post("/v1/tenants/{tenant_id}/coach/chat", response_model=ChatResponse)
async def coach_chat(tenant_id: str, request: ChatRequest):
    """Chat with AI business coach"""
    coach_service = get_coach_service()
    goals_service = get_goals_service()
    tasks_service = get_tasks_service()
    settings_service = get_settings_service()
    
    # Gather business context
    try:
        # Get connector data and check if it's real or sample data
        connector_data = await _fetch_connector_data(tenant_id)
        
        # Extract metadata from connector_data
        connector_metadata = connector_data.get("metadata", {})
        data_source_map = {}
        if "connector_names" in connector_metadata:
            # Build data source map from connector_data metadata
            for data_type in ["orders", "inventory", "customers"]:
                source_key = f"{data_type}_source"
                if connector_metadata.get(source_key):
                    data_source_map[data_type] = {
                        "connector_name": connector_metadata.get(source_key),
                        "record_count": len(connector_data.get(data_type, []))
                    }
        
        # Check if has real data from database (not in-memory mock)
        has_real_data = connector_data.get("has_data_connected", False)
        
        # Calculate health score
        calculator = HealthScoreCalculator(connector_data)
        health_score = calculator.calculate_overall_health()
        
        # Check if we have meaningful data
        total_orders = len(connector_data.get("orders", []))
        total_inventory = len(connector_data.get("inventory", []))
        total_customers = len(connector_data.get("customers", []))
        has_data_connected = has_real_data or (total_orders > 0 and total_inventory > 0)
        
        # Get goals
        goals = goals_service.get_goals(tenant_id, status=GoalStatus.ACTIVE)
        
        # Get tasks
        tasks = tasks_service.get_tasks(tenant_id, status=TaskStatus.TODO, limit=10)
        
        # Get business name from settings
        settings = settings_service.get_settings(tenant_id)
        business_name = settings.account.business_name or "your business"
        
        # Calculate key business metrics from actual data
        from datetime import datetime, timedelta
        now = datetime.now()
        thirty_days_ago = now - timedelta(days=30)
        
        orders = connector_data.get("orders", [])
        inventory = connector_data.get("inventory", [])
        customers = connector_data.get("customers", [])
        
        # Revenue metrics
        recent_orders = [o for o in orders if datetime.fromisoformat(o.get("created_at", now.isoformat())) >= thirty_days_ago]
        total_revenue_30d = sum(o.get("total_amount", 0) for o in recent_orders)
        avg_order_value = total_revenue_30d / len(recent_orders) if recent_orders else 0
        
        # Inventory metrics
        low_stock_items = [i for i in inventory if i.get("status") == "low_stock"]
        out_of_stock_items = [i for i in inventory if i.get("status") == "out_of_stock"]
        total_inventory_value = sum(i.get("quantity", 0) * i.get("unit_cost", 0) for i in inventory)
        total_inventory_quantity = sum(i.get("quantity", 0) for i in inventory)
        
        # Customer metrics
        vip_customers = [c for c in customers if c.get("segment") == "vip"]
        repeat_customers = [c for c in customers if c.get("total_orders", 0) > 1]
        repeat_rate = (len(repeat_customers) / len(customers) * 100) if customers else 0
        
        # Build context with ACTUAL data
        business_context = {
            "business_name": business_name,
            "industry": "retail",
            "has_data_connected": has_data_connected,
            "is_sample_data": not has_real_data,
            "data_sources": {
                "orders": total_orders,
                "inventory": total_inventory,
                "customers": total_customers,
            },
            "metadata": {
                "data_sources": data_source_map,
                "is_sample_data": not has_real_data,
            },
            "metrics": {
                "revenue_last_30_days": round(total_revenue_30d, 2),
                "orders_last_30_days": len(recent_orders),
                "avg_order_value": round(avg_order_value, 2),
                "total_inventory_items": total_inventory,
                "total_inventory_quantity": total_inventory_quantity,
                "low_stock_items": len(low_stock_items),
                "out_of_stock_items": len(out_of_stock_items),
                "total_inventory_value": round(total_inventory_value, 2),
                "total_customers": len(customers),
                "vip_customers": len(vip_customers),
                "repeat_customer_rate": round(repeat_rate, 1),
            },
            "alerts": {
                "low_stock_products": [i.get("product_name") for i in low_stock_items[:3]],
                "out_of_stock_products": [i.get("product_name") for i in out_of_stock_items[:3]],
            },
            "health_score": {
                "score": health_score.score,
                "trend": health_score.trend,
                "breakdown": {
                    "revenue": health_score.breakdown.revenue,
                    "operations": health_score.breakdown.operations,
                    "customer": health_score.breakdown.customer,
                }
            },
            "goals": [g.dict() for g in goals],
            "tasks": [t.dict() for t in tasks],
        }
        
        # Generate response
        response = await coach_service.chat(tenant_id, request, business_context)
        return response
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Coach error: {str(e)}")


@app.get("/v1/coach/personas")
async def list_coach_personas():
    """Get available coach personas for selection"""
    personas = []
    for persona_id, config in PersonaConfig.PERSONAS.items():
        personas.append({
            "id": persona_id,
            "name": config["name"],
            "emoji": config["emoji"],
            "description": config["description"],
            "expertise": config["expertise"],
            "tone": config["tone"],
        })
    return {"personas": personas}


@app.get("/v1/tenants/{tenant_id}/data-sources")
async def list_data_sources(tenant_id: str):
    """Get available data sources for the tenant"""
    connector_data = await _fetch_connector_data(tenant_id)
    
    data_sources = []
    
    # Check orders
    if connector_data.get("orders"):
        data_sources.append({
            "id": "orders",
            "name": "Orders & Revenue",
            "connector": "E-commerce",
            "record_count": len(connector_data["orders"]),
            "available": True,
        })
    
    # Check inventory
    if connector_data.get("inventory"):
        data_sources.append({
            "id": "inventory",
            "name": "Inventory Management",
            "connector": "Inventory System",
            "record_count": len(connector_data["inventory"]),
            "available": True,
        })
    
    # Check customers
    if connector_data.get("customers"):
        data_sources.append({
            "id": "customers",
            "name": "Customer Data",
            "connector": "CRM",
            "record_count": len(connector_data["customers"]),
            "available": True,
        })
    
    return {"data_sources": data_sources}


@app.post("/v1/tenants/{tenant_id}/coach/chat/stream/v2")
async def coach_chat_stream_v2(tenant_id: str, request: ChatRequest):
    """NEW: LangGraph-based streaming endpoint with native HITL and checkpointing"""
    logger.info(f"[coach_chat_stream_v2] 🎬 START - Tenant: {tenant_id}, Message: {request.message[:100]}...")
    
    from .coach_langgraph_workflow import get_coach_workflow
    from .coach_langgraph_streaming import stream_langgraph_to_sse
    
    # Gather business context
    goals_service = get_goals_service()
    tasks_service = get_tasks_service()
    settings_service = get_settings_service()
    
    try:
        connector_data = await _fetch_connector_data(tenant_id)
        calculator = HealthScoreCalculator(connector_data)
        health_score = calculator.calculate_overall_health()
        
        goals = goals_service.get_goals(tenant_id, status=GoalStatus.ACTIVE)
        tasks = tasks_service.get_tasks(tenant_id, status=TaskStatus.TODO, limit=10)
        settings = settings_service.get_settings(tenant_id)
        business_name = settings.account.business_name or "your business"
        
        # Build business context
        business_context = {
            "business_name": business_name,
            "health_score": {
                "score": health_score.score,
                "trend": health_score.trend,
                "breakdown": {
                    "revenue": health_score.breakdown.revenue,
                    "operations": health_score.breakdown.operations,
                    "customer": health_score.breakdown.customer,
                }
            },
            "goals": [g.dict() for g in goals],
            "tasks": [t.dict() for t in tasks],
        }
        
        # Prepare available data
        available_data = {
            "orders": connector_data.get("orders", []),
            "inventory": connector_data.get("inventory", []),
            "customers": connector_data.get("customers", [])
        }
        
        # Build initial state
        initial_state = {
            "tenant_id": tenant_id,
            "user_message": request.message,
            "conversation_history": [],
            "business_context": business_context,
            "available_data": available_data,
            "intent": None,
            "sub_tasks": [],
            "completed_tasks": [],
            "current_task_index": 0,
            "task_results": {},
            "report_id": None,
            "final_response": "",
            "pending_approval": None,
            "human_feedback": None,
        }
        
        # Get workflow
        workflow = get_coach_workflow()
        
        # Use thread_id for conversation persistence
        # Generate thread_id from first message or timestamp
        thread_id = f"thread-{tenant_id}-{int(datetime.now().timestamp())}"
        config = {
            "configurable": {
                "thread_id": thread_id
            }
        }
        
        # Stream workflow execution
        return StreamingResponse(
            stream_langgraph_to_sse(workflow, initial_state, config),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
                "X-Thread-ID": thread_id,
            }
        )
    
    except Exception as e:
        logger.error(f"[coach_chat_stream_v2] FATAL ERROR: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Coach streaming error: {str(e)}")


@app.post("/v1/tenants/{tenant_id}/coach/chat/stream")
async def coach_chat_stream(tenant_id: str, request: ChatRequest):
    """Stream conversational AI coach responses via Server-Sent Events with multi-agent orchestration (LEGACY)"""
    logger.info(f"[coach_chat_stream] 🎬 START - Tenant: {tenant_id}, Message: {request.message[:100]}...")
    
    # Use multi-agent coach for specialized queries
    coach = get_multi_agent_coach()
    goals_service = get_goals_service()
    tasks_service = get_tasks_service()
    settings_service = get_settings_service()
    
    # Gather business context (same as regular coach endpoint)
    try:
        logger.info(f"[coach_chat_stream] 📊 Step 1: Fetching connector data for tenant {tenant_id}")
        # Get connector data and check if it's real or sample data
        connector_data = await _fetch_connector_data(tenant_id)
        logger.info(f"[coach_chat_stream] ✅ Connector data fetched: {len(connector_data.get('orders', []))} orders, {len(connector_data.get('inventory', []))} inventory, {len(connector_data.get('customers', []))} customers")
        
        # Extract metadata from connector_data
        connector_metadata = connector_data.get("metadata", {})
        data_source_map = {}
        if "connector_names" in connector_metadata:
            # Build data source map from connector_data metadata
            for data_type in ["orders", "inventory", "customers"]:
                source_key = f"{data_type}_source"
                if connector_metadata.get(source_key):
                    data_source_map[data_type] = {
                        "connector_name": connector_metadata.get(source_key),
                        "record_count": len(connector_data.get(data_type, []))
                    }
        
        # Check if has real data from database (not in-memory mock)
        has_real_data = connector_data.get("has_data_connected", False)
        
        # Calculate health score
        calculator = HealthScoreCalculator(connector_data)
        health_score = calculator.calculate_overall_health()
        
        # Check if we have meaningful data
        total_orders = len(connector_data.get("orders", []))
        total_inventory = len(connector_data.get("inventory", []))
        total_customers = len(connector_data.get("customers", []))
        has_data_connected = has_real_data or (total_orders > 0 and total_inventory > 0)
        
        # Get goals
        goals = goals_service.get_goals(tenant_id, status=GoalStatus.ACTIVE)
        
        # Get tasks
        tasks = tasks_service.get_tasks(tenant_id, status=TaskStatus.TODO, limit=10)
        
        # Get business name from settings
        settings = settings_service.get_settings(tenant_id)
        business_name = settings.account.business_name or "your business"
        
        # Calculate key business metrics from actual data
        from datetime import datetime, timedelta
        now = datetime.now()
        thirty_days_ago = now - timedelta(days=30)
        
        orders = connector_data.get("orders", [])
        inventory = connector_data.get("inventory", [])
        customers = connector_data.get("customers", [])
        
        logger.info(f"[coach_chat_stream] 📊 Step 4: Creating execution plan like GitHub Copilot")
        
        # 🎯 GitHub Copilot-style Task Planning
        from .task_planner import get_task_planner
        task_planner = get_task_planner()
        
        # Create execution plan
        sub_tasks = task_planner.create_plan(request.message, {
            "orders": len(orders),
            "inventory": len(inventory),
            "customers": len(customers)
        })
        
        logger.info(f"[coach_chat_stream] 📋 Created plan with {len(sub_tasks)} sub-tasks:")
        for task in sub_tasks:
            logger.info(f"[coach_chat_stream]   - {task.description}")
        
        # Prepare data for execution
        available_data = {
            "orders": orders,
            "inventory": inventory,
            "customers": customers
        }
        
        # Also keep backward compatibility with orchestrator
        from .coach_orchestrator import CoachOrchestrator
        orchestrator = CoachOrchestrator()
        task_plan = orchestrator.analyze_intent(request.message, {
            "orders": len(orders),
            "inventory": len(inventory),
            "customers": len(customers)
        })
        
        logger.info(f"[coach_chat_stream] 🎯 Intent Analysis: {task_plan.task_type.value}")
        logger.info(f"[coach_chat_stream] 📋 Required data: {task_plan.data_requirements}")
        logger.info(f"[coach_chat_stream] ✅ Can execute: {task_plan.can_execute}, Missing: {task_plan.missing_data}")
        
        # 🎯 Execute sub-tasks step-by-step (GitHub Copilot style)
        # Store for later use in streaming
        metrics = {}
        alerts = {}
        task_results = {}
        
        # Store sub_tasks and task_planner for streaming
        execution_plan = {
            "sub_tasks": sub_tasks,
            "task_planner": task_planner,
            "available_data": available_data
        }
        
        logger.info(f"[coach_chat_stream] 📋 Created execution plan with {len(sub_tasks)} sub-tasks")
        
        logger.info(f"[coach_chat_stream] 📊 Step 5: Detecting business profile")
        # 🎯 NEW: Dynamically detect business profile
        from .business_profiler import BusinessProfiler
        
        # Get tenant metadata for profile detection
        tenant_metadata = {}
        try:
            logger.debug(f"[coach_chat_stream] Fetching tenant metadata from database")
            import psycopg2
            from psycopg2.extras import RealDictCursor
            pg_url = os.getenv("POSTGRES_URL")
            if not pg_url:
                pg_host = os.getenv("POSTGRES_HOST", "localhost")
                pg_port = os.getenv("POSTGRES_PORT", "5432")
                pg_db = os.getenv("POSTGRES_DB", "dyocense")
                pg_user = os.getenv("POSTGRES_USER", "dyocense")
                pg_pass = os.getenv("POSTGRES_PASSWORD", "pass@1234")
                pg_url = f"postgresql://{pg_user}:{pg_pass}@{pg_host}:{pg_port}/{pg_db}"
            
            conn = psycopg2.connect(pg_url, cursor_factory=RealDictCursor)
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT metadata FROM tenants.tenants WHERE tenant_id = %s",
                    (tenant_id,)
                )
                result = cur.fetchone()
                if result:
                    tenant_metadata = dict(result).get('metadata', {})
            conn.close()
        except Exception as e:
            logger.warning(f"Could not fetch tenant metadata: {e}")
        
        # Detect business profile from metadata and data patterns
        data_samples = {
            "orders": orders[:5] if orders else [],
            "inventory": inventory[:5] if inventory else [],
            "customers": customers[:5] if customers else []
        }
        
        business_profile = BusinessProfiler.get_profile(
            tenant_metadata=tenant_metadata,
            data_samples=data_samples
        )
        
        logger.info(f"[coach_chat_stream] 🏢 Business Profile Detected:")
        logger.info(f"[coach_chat_stream]   - Industry: {business_profile.industry}")
        logger.info(f"[coach_chat_stream]   - Business Type: {business_profile.business_type}")
        logger.info(f"[coach_chat_stream]   - Terminology: {business_profile.terminology}")
        logger.info(f"[coach_chat_stream] 📋 Metrics calculated: {list(metrics.keys())}")
        logger.info(f"[coach_chat_stream] 🚨 Alerts calculated: {list(alerts.keys())}")
        
        # Build context with ONLY RELEVANT data based on task type
        business_context = {
            "business_name": business_name,
            "industry": business_profile.industry,  # 🎯 Dynamic industry detection
            "business_type": business_profile.business_type,
            "terminology": business_profile.terminology,  # 🎯 Industry-specific terms
            "has_data_connected": has_data_connected,
            "is_sample_data": not has_real_data,
            "data_sources": {
                "orders": total_orders,
                "inventory": total_inventory,
                "customers": total_customers,
            },
            "metadata": {
                "data_sources": data_source_map,
                "is_sample_data": not has_real_data,
            },
            "metrics": metrics,  # 🎯 Dynamically calculated metrics
            "alerts": alerts,    # 🎯 Dynamically generated alerts
            "task_type": task_plan.task_type.value,  # 🎯 Pass task type to prompt
            "execution_plan": execution_plan,  # 🎯 Sub-tasks to execute during streaming
            "health_score": {
                "score": health_score.score,
                "trend": health_score.trend,
                "breakdown": {
                    "revenue": health_score.breakdown.revenue,
                    "operations": health_score.breakdown.operations,
                    "customer": health_score.breakdown.customer,
                }
            },
            "goals": [g.dict() for g in goals],
            "tasks": [t.dict() for t in tasks],
        }
        
        # Create local run log for this conversation turn
        logger.info(f"[coach_chat_stream] 📝 Creating run log")
        run_id = create_runlog(tenant_id, input_text=request.message, persona=request.persona, metadata={
            "source": "coach_chat_stream"
        })
        logger.info(f"[coach_chat_stream] ✅ Run log created: {run_id}")
        
        # Log business context for debugging
        logger.info(f"[coach_chat_stream] 📊 Step 6: Business Context Summary:")
        logger.info(f"[coach_chat_stream]   - Has Real Data: {has_data_connected}")
        logger.info(f"[coach_chat_stream]   - Data Counts: {total_orders} orders, {total_inventory} inventory, {total_customers} customers")
        logger.info(f"[coach_chat_stream]   - Metrics Calculated: {list(business_context['metrics'].keys())}")
        logger.info(f"[coach_chat_stream]   - Health Score: {business_context['health_score']['score']}/100")
        logger.info(f"[coach_chat_stream]   - Goals: {len(business_context['goals'])}, Tasks: {len(business_context['tasks'])}")

        # Create event generator for SSE streaming
        logger.info(f"[coach_chat_stream] 🚀 Step 7: Starting streaming response with task execution")
        async def event_generator():
            try:
                # 🎯 PHASE 1: Execute sub-tasks with progress updates (GitHub Copilot style)
                logger.info(f"[coach_chat_stream] � Phase 1: Executing {len(sub_tasks)} sub-tasks...")
                
                task_results_stream = {}
                for idx, task in enumerate(sub_tasks):
                    # Send progress update
                    progress_msg = f"{task.description}\n"
                    yield f"data: {json.dumps({'delta': progress_msg, 'done': False, 'metadata': {'phase': 'task_execution', 'task_id': task.id}})}\n\n"
                    
                    # Execute task
                    completed_task = task_planner.execute_task(task, available_data)

                    if completed_task.status.value == "awaiting_human":
                        logger.info(f"[coach_chat_stream] ⏸ Task {task.id} awaiting human review")
                        review_info = completed_task.result or {}
                        try:
                            # Store remaining execution context to resume later
                            remaining_sub_tasks = sub_tasks[idx+1:]
                            _rid = review_info.get('review_id')
                            if _rid:
                                PENDING_EXECUTIONS[_rid] = {
                                    'tenant_id': tenant_id,
                                    'awaiting_task_id': task.id,
                                    'awaiting_task_description': task.description,
                                    'remaining_tasks': remaining_sub_tasks,
                                    'available_data': available_data,
                                    'business_context': business_context,
                                    'task_results_stream': task_results_stream,
                                    'task_planner': task_planner,
                                    'run_id': run_id,
                                    'request_message': request.message,
                                    'business_name': business_name,
                                    'conversation_history': request.conversation_history or [],
                                }
                                logger.info(f"[coach_chat_stream] 💾 Stored pending execution for review_id={_rid} with {len(remaining_sub_tasks)} remaining tasks")
                            else:
                                logger.warning("[coach_chat_stream] Missing review_id in awaiting_human result; cannot store pending execution context")
                        except Exception as store_err:
                            logger.warning(f"[coach_chat_stream] Failed to store pending execution: {store_err}")
                        # Send awaiting human update and stop further execution
                        yield f"data: {json.dumps({'delta': '⏸ Awaiting your approval\n', 'done': False, 'metadata': {'phase': 'task_execution', 'task_id': task.id, 'task_status': 'awaiting_human', 'review_id': review_info.get('review_id'), 'proposed_result': review_info.get('proposed_result')}})}\n\n"
                        # End the stream for now; frontend will call review endpoint and user can trigger next action
                        yield f"data: {json.dumps({'delta': '', 'done': True, 'metadata': {'phase': 'task_execution', 'task_id': task.id, 'task_status': 'awaiting_human'}})}\n\n"
                        return
                    
                    if completed_task.status.value == "completed":
                        logger.info(f"[coach_chat_stream] ✅ Task {task.id} completed")
                        task_results_stream[task.id] = completed_task.result
                        
                        # Update metrics for business_context
                        if completed_task.result:
                            business_context["metrics"].update(completed_task.result)
                        
                        # Send completion update
                        yield f"data: {json.dumps({'delta': '✓ ', 'done': False, 'metadata': {'phase': 'task_execution', 'task_status': 'completed'}})}\n\n"
                    else:
                        logger.error(f"[coach_chat_stream] ❌ Task {task.id} failed")
                        yield f"data: {json.dumps({'delta': '✗ Failed\n', 'done': False, 'metadata': {'phase': 'task_execution', 'task_status': 'failed'}})}\n\n"
                
                # Add task results to business context
                business_context["task_results"] = task_results_stream
                business_context["sub_tasks_completed"] = [t.id for t in sub_tasks if t.status.value == "completed"]
                
                # 🎯 PHASE 1.5: Generate downloadable report with agent thinking and evidence
                logger.info(f"[coach_chat_stream] 📊 Generating downloadable report...")
                try:
                    report_generator = get_report_generator()
                    
                    # Create report with sections, agent thoughts, and evidence
                    from .report_generator import BusinessReport, ReportSection, AgentThought, Evidence
                    
                    report = BusinessReport(
                        title="Business Analysis Report",
                        business_name=business_name,
                        report_type="comprehensive_analysis"
                    )
                    
                    # Build report from task results
                    for task in sub_tasks:
                        if task.status.value == "completed" and task.result:
                            result = task.result
                            
                            # Extract agent thoughts and evidence from result
                            agent_thoughts = []
                            if "agent_thoughts" in result:
                                for thought_data in result["agent_thoughts"]:
                                    agent_thoughts.append(AgentThought(
                                        agent_name=thought_data.get("agent", "Analysis Agent"),
                                        thought=thought_data.get("thought", ""),
                                        action=thought_data.get("action", ""),
                                        observation=thought_data.get("observation", ""),
                                        data_source=thought_data.get("data_source", "")
                                    ))
                            
                            evidence_list = []
                            if "evidence" in result:
                                for ev_data in result["evidence"]:
                                    evidence_list.append(Evidence(
                                        claim=ev_data.get("claim", ""),
                                        data_source=ev_data.get("data_source", ""),
                                        calculation=ev_data.get("calculation", ""),
                                        raw_value=ev_data.get("value", ""),
                                        confidence=ev_data.get("confidence", 1.0)
                                    ))
                            
                            # Create section for this task
                            section = ReportSection(
                                title=task.description,
                                content=f"Analysis completed for: {task.description}",
                                data=result,
                                insights=[],
                                recommendations=[],
                                agent_thoughts=agent_thoughts,
                                evidence=evidence_list
                            )
                            report.add_section(section)
                    
                    # Set summary
                    report.set_summary(f"Analyzed data for {business_name} across {len(sub_tasks)} dimensions.")
                    
                    # Store report for download
                    if tenant_id not in TENANT_REPORTS:
                        TENANT_REPORTS[tenant_id] = {}
                    
                    TENANT_REPORTS[tenant_id][report.report_id] = {
                        "report": report,
                        "original_query": request.message,
                        "created_at": datetime.now().isoformat()
                    }
                    
                    # Send report availability message
                    report_msg = f"\n📊 **Report Generated:** [Download Report](/v1/tenants/{tenant_id}/reports/download?report_id={report.report_id}&format=html) | Report ID: `{report.report_id}`\n\n"
                    yield f"data: {json.dumps({'delta': report_msg, 'done': False, 'metadata': {'phase': 'report_generated', 'report_id': report.report_id}})}\n\n"
                    
                    logger.info(f"[coach_chat_stream] ✅ Report generated: {report.report_id}")
                except Exception as report_error:
                    logger.error(f"[coach_chat_stream] ⚠️ Failed to generate report: {report_error}")
                    # Continue anyway - report is nice-to-have
                
                # Send separator before analysis
                yield f"data: {json.dumps({'delta': '\n🤖 Analyzing results...\n\n', 'done': False, 'metadata': {'phase': 'analysis'}})}\n\n"
                
                # 🎯 PHASE 2: Stream coach response with analysis
                logger.info(f"[coach_chat_stream] 💬 Phase 2: Streaming coach response")
                async for chunk in coach.stream_response(
                    tenant_id=tenant_id,
                    user_message=request.message,
                    business_context=business_context,
                    conversation_history=request.conversation_history or []
                ):
                    # Accumulate output and record tool events
                    try:
                        if getattr(chunk, "delta", None):
                            runlog_append_output(tenant_id, run_id, getattr(chunk, "delta"))
                        meta = getattr(chunk, "metadata", {}) or {}
                        if isinstance(meta, dict) and meta.get("tool_event"):
                            runlog_append_event(tenant_id, run_id, meta["tool_event"]) 
                        # Inject local run_url on final chunk
                        if getattr(chunk, "done", False):
                            # finalize the run and attach run_url
                            run_url = f"/v1/tenants/{tenant_id}/coach/runs/{run_id}"
                            runlog_finalize(tenant_id, run_id, metadata={"run_url": run_url})
                            # augment chunk metadata
                            meta = dict(meta)
                            meta.setdefault("run_url", run_url)
                            try:
                                payload = {"delta": chunk.delta, "done": True, "metadata": meta}
                                yield f"data: {json.dumps(payload)}\n\n"
                                continue
                            except Exception:
                                pass
                    except Exception:
                        # ignore run log errors
                        pass

                    # Default: pass-through
                    yield f"data: {chunk.model_dump_json()}\n\n"
            except Exception as e:
                # Send error as final chunk
                logger.error(f"[coach_chat_stream] ❌ Error in event generator: {str(e)}", exc_info=True)
                error_chunk = {
                    "delta": f"\n\nI apologize, but I encountered an error: {str(e)}",
                    "done": True,
                    "metadata": {"error": str(e)}
                }
                yield f"data: {json.dumps(error_chunk)}\n\n"
        
        logger.info(f"[coach_chat_stream] ✅ Returning streaming response")
        return StreamingResponse(
            event_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",  # Disable nginx buffering
            }
        )
        
    except Exception as e:
        logger.error(f"[coach_chat_stream] ❌ FATAL ERROR: {str(e)}", exc_info=True)
        logger.error(f"[coach_chat_stream] Tenant: {tenant_id}, Message: {request.message}")
        raise HTTPException(status_code=500, detail=f"Coach streaming error: {str(e)}")


@app.get("/v1/tenants/{tenant_id}/coach/runs")
async def list_coach_runs(tenant_id: str, limit: int = Query(20, ge=1, le=100)):
    """List recent local coach runs (no LangSmith required)."""
    items = [r.model_dump() for r in runlog_list(tenant_id, limit=limit)]
    return {"items": items, "count": len(items)}


@app.get("/v1/tenants/{tenant_id}/coach/runs/{run_id}")
async def get_coach_run(tenant_id: str, run_id: str):
    """Fetch a single local coach run log by id."""
    run = runlog_get(tenant_id, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    return run


@app.get("/v1/tenants/{tenant_id}/coach/history", response_model=List[ChatMessage])
async def get_coach_history(tenant_id: str, limit: int = Query(50, ge=1, le=100)):
    """Get chat history with AI coach"""
    coach_service = get_coach_service()
    history = coach_service.get_conversation_history(tenant_id, limit=limit)
    return history


# ===================================
# Analytics Endpoints
# ===================================

@app.get("/v1/tenants/{tenant_id}/analytics/health-history", response_model=List[HealthScoreHistoryPoint])
async def get_health_score_history(
    tenant_id: str,
    days: int = Query(30, ge=7, le=365),
    interval: str = Query('daily', regex='^(daily|weekly)$'),
):
    """Get health score historical data"""
    analytics_service = get_analytics_service()
    history = analytics_service.get_health_score_history(tenant_id, days=days, interval=interval)
    return history


@app.get("/v1/tenants/{tenant_id}/analytics/goal-progress", response_model=List[GoalProgressPoint])
async def get_goal_progress_analytics(tenant_id: str):
    """Get goal progress analytics"""
    analytics_service = get_analytics_service()
    goals_service = get_goals_service()
    
    # Get active goals
    goals = goals_service.get_goals(tenant_id, status=GoalStatus.ACTIVE)
    goals_data = [g.dict() for g in goals]
    
    # Get progress snapshot
    progress = analytics_service.get_goal_progress_snapshot(goals_data)
    return progress


@app.get("/v1/tenants/{tenant_id}/analytics/task-completion", response_model=List[TaskCompletionStats])
async def get_task_completion_analytics(
    tenant_id: str,
    days: int = Query(30, ge=7, le=90),
):
    """Get task completion statistics"""
    analytics_service = get_analytics_service()
    stats = analytics_service.get_task_completion_stats(tenant_id, days=days)
    return stats


@app.get("/v1/tenants/{tenant_id}/analytics/category-breakdown")
async def get_category_breakdown(
    tenant_id: str,
    type: str = Query(..., regex='^(goals|tasks|revenue)$'),
):
    """
    Get category breakdown for visualization
    
    Args:
        type: 'goals', 'tasks', or 'revenue'
    """
    analytics_service = get_analytics_service()
    
    if type == 'goals':
        goals_service = get_goals_service()
        goals = goals_service.get_goals(tenant_id, status=GoalStatus.ACTIVE)
        items = [g.dict() for g in goals]
        breakdown = analytics_service.get_category_breakdown(items, category_field='category')
        
    elif type == 'tasks':
        tasks_service = get_tasks_service()
        tasks = tasks_service.get_tasks(tenant_id, status=TaskStatus.TODO)
        items = [t.dict() for t in tasks]
        breakdown = analytics_service.get_category_breakdown(items, category_field='category')
        
    else:  # revenue
        # Get revenue from connector data
        connector_data = await _fetch_connector_data(tenant_id)
        orders = connector_data.get('orders', [])
        
        # Group by product category (mock for now)
        # In production, this would come from actual order line items
        breakdown = [
            CategoryBreakdown(category="Products", value=sum(o.get('total_amount', 0) * 0.7 for o in orders), percentage=70),
            CategoryBreakdown(category="Services", value=sum(o.get('total_amount', 0) * 0.2 for o in orders), percentage=20),
            CategoryBreakdown(category="Other", value=sum(o.get('total_amount', 0) * 0.1 for o in orders), percentage=10),
        ]
    
    return breakdown


@app.post("/v1/tenants/{tenant_id}/analytics/record-health-score")
async def record_health_score_analytics(tenant_id: str):
    """Record current health score for historical tracking"""
    analytics_service = get_analytics_service()
    
    # Get current health score
    connector_data = await _fetch_connector_data(tenant_id)
    calculator = HealthScoreCalculator(connector_data)
    health_score = calculator.calculate_overall_health()
    
    # Record in analytics
    point = analytics_service.record_health_score(
        tenant_id,
        float(health_score.score if health_score.score is not None else 0.0),
        {
            'revenue': float(health_score.breakdown.revenue if health_score.breakdown.revenue is not None else 0.0),
            'operations': float(health_score.breakdown.operations if health_score.breakdown.operations is not None else 0.0),
            'customer': float(health_score.breakdown.customer if health_score.breakdown.customer is not None else 0.0),
        }
    )
    
    return {
        "message": "Health score recorded",
        "point": point
    }


# ============================================================================
# Achievements Endpoints
# ============================================================================

@app.get("/v1/tenants/{tenant_id}/achievements", response_model=List[Achievement])
async def get_achievements(tenant_id: str):
    """Get all achievements with progress for tenant"""
    achievements_service = get_achievements_service()
    return achievements_service.get_achievements(tenant_id)


@app.post("/v1/tenants/{tenant_id}/achievements/check")
async def check_achievements(tenant_id: str):
    """
    Check and update achievement progress based on current data.
    Returns newly unlocked achievements.
    """
    achievements_service = get_achievements_service()
    goals_service = get_goals_service()
    tasks_service = get_tasks_service()
    analytics_service = get_analytics_service()
    
    # Gather current stats
    goals = goals_service.get_goals(tenant_id)
    tasks = tasks_service.get_tasks(tenant_id)
    
    # Count completed goals
    completed_goals = sum(1 for g in goals if g.status == GoalStatus.COMPLETED)
    
    # Count completed tasks
    completed_tasks = sum(1 for t in tasks if t.status == TaskStatus.COMPLETED)
    
    # Get current health score
    connector_data = await _fetch_connector_data(tenant_id)
    calculator = HealthScoreCalculator(connector_data)
    health_score_response = calculator.calculate_overall_health()
    
    # Count active goals
    active_goals = sum(1 for g in goals if g.status == GoalStatus.ACTIVE)
    
    # Get streak (would come from login/activity tracking in production)
    streak_days = 4  # Sample value
    
    # Count connected data sources (would come from connector registry)
    data_sources = 2  # Sample: GrandNode + Salesforce
    
    # Update progress
    newly_unlocked = achievements_service.update_progress(
        tenant_id=tenant_id,
        goals_completed=completed_goals,
        tasks_completed=completed_tasks,
        streak_days=streak_days,
        health_score=int(health_score_response.score),
        active_goals=active_goals,
        data_sources=data_sources,
    )
    
    # Calculate total XP
    total_xp = achievements_service.calculate_total_xp(tenant_id)
    
    return {
        "newly_unlocked": newly_unlocked,
        "total_xp": total_xp,
        "unlocked_count": len(achievements_service.unlocked_achievements.get(tenant_id, [])),
    }


@app.post("/v1/tenants/{tenant_id}/achievements/{achievement_id}/share")
async def share_achievement(tenant_id: str, achievement_id: str):
    """Track achievement share"""
    achievements_service = get_achievements_service()
    success = achievements_service.share_achievement(tenant_id, achievement_id)
    
    return {
        "success": success,
        "shares": achievements_service.progress_data.get(tenant_id, AchievementProgress()).shares,
    }


@app.get("/v1/tenants/{tenant_id}/achievements/xp")
async def get_total_xp(tenant_id: str):
    """Get total XP earned"""
    achievements_service = get_achievements_service()
    total_xp = achievements_service.calculate_total_xp(tenant_id)
    unlocked_count = len(achievements_service.unlocked_achievements.get(tenant_id, []))
    total_count = len(achievements_service.achievement_definitions)
    
    return {
        "total_xp": total_xp,
        "unlocked_count": unlocked_count,
        "total_count": total_count,
        "completion_percentage": round((unlocked_count / total_count) * 100) if total_count > 0 else 0,
    }


# ============================================================================
# Settings Endpoints
# ============================================================================

@app.get("/v1/tenants/{tenant_id}/settings", response_model=TenantSettings)
async def get_tenant_settings(tenant_id: str):
    """Get all settings for tenant"""
    settings_service = get_settings_service()
    return settings_service.get_settings(tenant_id)


@app.put("/v1/tenants/{tenant_id}/settings")
async def update_tenant_settings(tenant_id: str, settings: TenantSettings):
    """Update all settings for tenant"""
    settings_service = get_settings_service()
    return settings_service.update_all_settings(tenant_id, settings)


@app.put("/v1/tenants/{tenant_id}/settings/notifications")
async def update_notification_settings(
    tenant_id: str,
    settings: NotificationSettings
):
    """Update notification settings"""
    settings_service = get_settings_service()
    return settings_service.update_notifications(tenant_id, settings)


@app.put("/v1/tenants/{tenant_id}/settings/account")
async def update_account_settings(
    tenant_id: str,
    settings: AccountSettings
):
    """Update account settings"""
    settings_service = get_settings_service()
    return settings_service.update_account(tenant_id, settings)


@app.put("/v1/tenants/{tenant_id}/settings/appearance")
async def update_appearance_settings(
    tenant_id: str,
    settings: AppearanceSettings
):
    """Update appearance settings"""
    settings_service = get_settings_service()
    return settings_service.update_appearance(tenant_id, settings)


@app.put("/v1/tenants/{tenant_id}/settings/integrations")
async def update_integration_settings(
    tenant_id: str,
    settings: IntegrationSettings
):
    """Update integration settings"""
    settings_service = get_settings_service()
    return settings_service.update_integrations(tenant_id, settings)


# ===================================
# Connector Marketplace Endpoints
# ===================================

@app.get("/v1/tenants/{tenant_id}/connectors/recommendations")
async def get_connector_recommendations(tenant_id: str):
    """
    Get personalized connector recommendations based on business profile and synced data.
    
    Returns dynamic connector presets tailored to:
    - Business type (restaurant, retail, ecommerce, etc.)
    - Current data gaps (missing orders, inventory, customers)
    - Industry best practices
    """
    try:
        # Fetch tenant profile to understand business type
        business_profile = {}
        industry = None
        business_type = None
        
        try:
            import psycopg2
            from psycopg2.extras import RealDictCursor
            
            pg_url = os.getenv("POSTGRES_URL")
            if not pg_url:
                pg_host = os.getenv("POSTGRES_HOST", "localhost")
                pg_port = os.getenv("POSTGRES_PORT", "5432")
                pg_db = os.getenv("POSTGRES_DB", "dyocense")
                pg_user = os.getenv("POSTGRES_USER", "dyocense")
                pg_pass = os.getenv("POSTGRES_PASSWORD", "pass@1234")
                pg_url = f"postgresql://{pg_user}:{pg_pass}@{pg_host}:{pg_port}/{pg_db}"
            
            conn = psycopg2.connect(pg_url, cursor_factory=RealDictCursor)
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT metadata FROM accounts.tenants WHERE tenant_id = %s",
                    (tenant_id,)
                )
                result = cur.fetchone()
                if result:
                    metadata = dict(result).get('metadata', {})
                    business_profile = metadata.get('business_profile', {})
                    industry = business_profile.get('industry')
                    business_type = business_profile.get('business_type')
            conn.close()
        except Exception as e:
            logger.warning(f"Could not fetch tenant profile: {e}")
        
        # Fetch current connector data to understand gaps
        connector_data = await _fetch_connector_data(tenant_id)
        has_orders = len(connector_data.get('orders', [])) > 0
        has_inventory = len(connector_data.get('inventory', [])) > 0
        has_customers = len(connector_data.get('customers', [])) > 0
        has_products = len(connector_data.get('products', [])) > 0
        
        # Fetch existing connectors to avoid duplication
        existing_connector_types = set()
        try:
            from packages.connectors.repository_postgres import ConnectorRepositoryPG
            repo = ConnectorRepositoryPG()
            existing_connectors = repo.list_by_tenant(tenant_id)
            existing_connector_types = {c.connector_type for c in existing_connectors}
        except Exception as e:
            logger.warning(f"Could not fetch existing connectors: {e}")
        
        # Build personalized recommendations
        recommendations = []
        
        # Always offer CSV upload as the easiest starting point
        if 'csv_upload' not in existing_connector_types:
            recommendations.append({
                "id": "csv_upload",
                "label": "CSV/Excel Upload",
                "description": "Upload a CSV or Excel file from your device, or provide a URL to fetch data automatically.",
                "icon": "📊",
                "category": "files",
                "priority": 1,
                "reason": "Quick start - upload your existing spreadsheets",
                "fields": [
                    {
                        "name": "uploaded_file",
                        "label": "Upload file",
                        "type": "file",
                        "accept": ".csv,.xlsx,.xls",
                        "helper": "Select a CSV or Excel file from your computer"
                    },
                    {
                        "name": "file_url",
                        "label": "Or provide a URL (optional)",
                        "placeholder": "https://example.com/export.csv",
                        "helper": "If you have a hosted file that updates regularly"
                    }
                ]
            })
        
        # Google Drive for collaborative teams
        if 'google-drive' not in existing_connector_types and business_profile.get('team_size', '1') != '1':
            recommendations.append({
                "id": "google-drive",
                "label": "Google Drive",
                "description": "Bring in spreadsheets from a shared Drive folder.",
                "icon": "📁",
                "category": "cloud",
                "priority": 2,
                "reason": "Your team can collaborate on shared spreadsheets",
                "fields": [
                    {"name": "folder_id", "label": "Folder ID", "placeholder": "e.g. 1AbCDriveFolderID"},
                    {
                        "name": "service_account_json",
                        "label": "Service account JSON",
                        "type": "textarea",
                        "placeholder": '{ "type": "service_account", ... }',
                        "helper": "Create a Google Cloud service account and share the folder with it."
                    }
                ]
            })
        
        # E-commerce connectors for online businesses
        if business_type in ['ecommerce', 'retail', 'eCommerce', 'Retail']:
            if 'shopify' not in existing_connector_types and not has_orders:
                recommendations.append({
                    "id": "shopify",
                    "label": "Shopify",
                    "description": "Connect your Shopify storefront for orders, carts, and customers.",
                    "icon": "🛍️",
                    "category": "ecommerce",
                    "priority": 3,
                    "reason": f"Perfect for {business_type} businesses - sync orders and customers automatically",
                    "fields": [
                        {"name": "store_url", "label": "Store URL", "placeholder": "https://yourstore.myshopify.com"},
                        {"name": "api_key", "label": "Admin API access token", "type": "textarea"}
                    ]
                })
            
            if 'grandnode' not in existing_connector_types and not has_orders:
                recommendations.append({
                    "id": "grandnode",
                    "label": "GrandNode",
                    "description": "Sync sales and catalog data from your GrandNode shop.",
                    "icon": "🛒",
                    "category": "ecommerce",
                    "priority": 4,
                    "reason": "Alternative e-commerce platform for sales tracking",
                    "fields": [
                        {"name": "store_url", "label": "Store URL", "placeholder": "https://shop.example.com"},
                        {"name": "api_key", "label": "API key", "type": "text"}
                    ]
                })
        
        # ERP for businesses needing inventory/operations management
        if business_type in ['manufacturing', 'retail', 'restaurant', 'Manufacturing', 'Retail', 'Restaurant'] or not has_inventory:
            if 'erpnext' not in existing_connector_types:
                priority = 3 if not has_inventory else 5
                reason = "Sync inventory, orders, and suppliers" if not has_inventory else "Advanced ERP integration for comprehensive data"
                recommendations.append({
                    "id": "erpnext",
                    "label": "ERPNext",
                    "description": "Connect your ERPNext ERP system to sync inventory, sales orders, and supplier data automatically.",
                    "icon": "⚙️",
                    "category": "erp",
                    "priority": priority,
                    "reason": reason,
                    "fields": [
                        {
                            "name": "api_url",
                            "label": "ERPNext URL",
                            "placeholder": "https://erp.example.com",
                            "helper": "Your ERPNext instance URL (e.g., https://erp.yourcompany.com)"
                        },
                        {
                            "name": "api_key",
                            "label": "API Key",
                            "type": "text",
                            "helper": "Found in User Settings → API Access after generating keys"
                        },
                        {
                            "name": "api_secret",
                            "label": "API Secret",
                            "type": "textarea",
                            "helper": "⚠️ Copy this immediately when generating keys - it's only shown once! Go to: User → Settings → API Access → Generate Keys"
                        }
                    ]
                })
        
        # Sort by priority
        recommendations.sort(key=lambda x: x.get('priority', 999))
        
        return {
            "recommendations": recommendations,
            "business_profile": {
                "industry": industry,
                "business_type": business_type,
                "team_size": business_profile.get('team_size')
            },
            "data_status": {
                "has_orders": has_orders,
                "has_inventory": has_inventory,
                "has_customers": has_customers,
                "has_products": has_products
            },
            "existing_connectors": list(existing_connector_types),
            "message": f"Showing {len(recommendations)} personalized connector recommendations"
        }
    
    except Exception as e:
        logger.error(f"Error fetching connector recommendations: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error fetching recommendations: {str(e)}")


@app.get("/v1/marketplace/connectors")
async def get_marketplace_connectors(
    category: Optional[str] = Query(None, description="Filter by category (ecommerce, finance, crm, etc)"),
    tier: Optional[str] = Query(None, description="Filter by tier (free, standard, premium, enterprise)"),
    popular: Optional[bool] = Query(None, description="Filter to popular connectors only"),
    search: Optional[str] = Query(None, description="Search query for name/description"),
):
    """
    Get available connectors from the marketplace
    
    Browse the connector catalog to discover integrations for your business.
    Filter by category, pricing tier, popularity, or search by keywords.
    """
    try:
        from packages.connectors.marketplace import marketplace, ConnectorCategory, ConnectorTier
        
        # Apply filters
        if search:
            connectors = marketplace.search(search)
        elif category:
            try:
                cat = ConnectorCategory(category)
                connectors = marketplace.get_by_category(cat)
            except ValueError:
                connectors = marketplace.get_all()
        elif tier:
            try:
                tier_enum = ConnectorTier(tier)
                connectors = marketplace.get_by_tier(tier_enum)
            except ValueError:
                connectors = marketplace.get_all()
        else:
            connectors = marketplace.get_all()
        
        # Filter by popularity if requested
        if popular is True:
            connectors = [c for c in connectors if c.get('popular', False)]
        
        return {
            "connectors": connectors,
            "total": len(connectors),
            "categories": [c.value for c in ConnectorCategory if c != ConnectorCategory.ALL],
            "tiers": [t.value for t in ConnectorTier],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching marketplace: {str(e)}")


@app.get("/v1/marketplace/connectors/{connector_id}")
async def get_marketplace_connector_detail(connector_id: str):
    """
    Get detailed information about a specific connector
    
    Returns full details including setup instructions, config fields,
    features, limitations, and pricing information.
    """
    try:
        from packages.connectors.marketplace import marketplace
        
        connector = marketplace.get_by_id(connector_id)
        if not connector:
            raise HTTPException(status_code=404, detail=f"Connector '{connector_id}' not found")
        
        return connector
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching connector: {str(e)}")


@app.get("/v1/marketplace/connectors/{connector_id}/config")
async def get_connector_config_fields(connector_id: str):
    """
    Get configuration fields required for a connector
    
    Returns the form fields needed to set up this connector,
    including field types, labels, validation rules, and help text.
    """
    try:
        from packages.connectors.marketplace import marketplace
        
        config_fields = marketplace.get_config_fields(connector_id)
        return {
            "connector_id": connector_id,
            "config_fields": config_fields
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching config: {str(e)}")


@app.get("/v1/marketplace/categories")
async def get_marketplace_categories():
    """
    Get all connector categories
    
    Returns the list of categories used to organize connectors
    in the marketplace (ecommerce, finance, crm, etc).
    """
    try:
        from packages.connectors.marketplace import ConnectorCategory, marketplace
        
        # Get category counts
        category_counts = {}
        all_connectors = marketplace.get_all()
        for connector in all_connectors:
            cat = connector['category']
            category_counts[cat] = category_counts.get(cat, 0) + 1
        
        return {
            "categories": [
                {
                    "id": cat.value,
                    "name": cat.value.replace('_', ' ').title(),
                    "count": category_counts.get(cat.value, 0)
                }
                for cat in ConnectorCategory
                if cat != ConnectorCategory.ALL
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching categories: {str(e)}")


@app.get("/v1/tenants/{tenant_id}/connectors/connected")
async def get_connected_connectors(tenant_id: str):
    """
    Get connectors that are currently connected for this tenant
    
    Returns a list of active integrations with sync status,
    last sync time, and data availability.
    """
    # TODO: Integrate with actual connector repository
    # For now, return empty list
    return {
        "connectors": [],
        "total": 0,
        "has_real_data": False
    }


@app.post("/v1/tenants/{tenant_id}/connectors/connect")
async def connect_connector(
    tenant_id: str,
    request: BaseModel  # TODO: Define ConnectorConnectionRequest model
):
    """
    Connect a new data source
    
    Creates a new connector instance with the provided configuration.
    Validates credentials and initiates the first data sync.
    """
    # TODO: Implement connector connection logic
    # 1. Validate connector_type exists in marketplace
    # 2. Encrypt credentials
    # 3. Test connection
    # 4. Create connector record
    # 5. Trigger initial sync
    
    raise HTTPException(status_code=501, detail="Connector connection not yet implemented")


@app.delete("/v1/tenants/{tenant_id}/connectors/{connector_id}")
async def disconnect_connector(tenant_id: str, connector_id: str):
    """
    Disconnect a data source
    
    Removes the connector and stops future data syncs.
    Historical data is retained but will no longer be updated.
    """
    # TODO: Implement connector disconnection logic
    raise HTTPException(status_code=501, detail="Connector disconnection not yet implemented")


@app.post("/v1/tenants/{tenant_id}/connectors/{connector_id}/sync")
async def trigger_connector_sync(tenant_id: str, connector_id: str):
    """
    Manually trigger a data sync
    
    Initiates an immediate sync for this connector.
    Useful for testing or getting the latest data on-demand.
    """
    # TODO: Implement manual sync trigger
    raise HTTPException(status_code=501, detail="Manual sync not yet implemented")


@app.get("/v1/tenants/{tenant_id}/reports/{report_type}")
async def generate_downloadable_report(
    tenant_id: str,
    report_type: str,
    format: str = Query("json", regex="^(json|markdown|html)$")
):
    """
    Generate downloadable business report with charts and visualizations
    
    Args:
        tenant_id: Tenant ID
        report_type: Type of report (inventory, revenue, customer, health)
        format: Output format (json, markdown, html)
    
    Returns:
        Structured report with charts, tables, insights, and recommendations
    """
    try:
        from .report_generator import ReportGenerator, ReportFormat
        from .business_profiler import BusinessProfiler
        from fastapi.responses import Response
        
        # Get connector data
        connector_data = await _fetch_connector_data(tenant_id)
        
        # Get business profile
        orders = connector_data.get("orders", [])
        inventory = connector_data.get("inventory", [])
        customers = connector_data.get("customers", [])
        
        tenant_metadata = {}
        try:
            import psycopg2
            from psycopg2.extras import RealDictCursor
            pg_url = os.getenv("POSTGRES_URL")
            if not pg_url:
                pg_host = os.getenv("POSTGRES_HOST", "localhost")
                pg_port = os.getenv("POSTGRES_PORT", "5432")
                pg_db = os.getenv("POSTGRES_DB", "dyocense")
                pg_user = os.getenv("POSTGRES_USER", "dyocense")
                pg_pass = os.getenv("POSTGRES_PASSWORD", "pass@1234")
                pg_url = f"postgresql://{pg_user}:{pg_pass}@{pg_host}:{pg_port}/{pg_db}"
            
            conn = psycopg2.connect(pg_url, cursor_factory=RealDictCursor)
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT metadata FROM tenants.tenants WHERE tenant_id = %s",
                    (tenant_id,)
                )
                result = cur.fetchone()
                if result:
                    tenant_metadata = dict(result).get('metadata', {})
            conn.close()
        except Exception as e:
            logger.warning(f"Could not fetch tenant metadata: {e}")
        
        data_samples = {
            "orders": orders[:5] if orders else [],
            "inventory": inventory[:5] if inventory else [],
            "customers": customers[:5] if customers else []
        }
        
        business_profile = BusinessProfiler.get_profile(
            tenant_metadata=tenant_metadata,
            data_samples=data_samples
        )
        
        # Get settings for business name
        settings_service = get_settings_service()
        settings = settings_service.get_settings(tenant_id)
        business_name = settings.account.business_name or "Your Business"
        
        # Generate report based on type
        if report_type == "inventory":
            # Run inventory analysis
            from .analysis_tools import analyze_inventory_data
            from datetime import datetime, timedelta
            
            now = datetime.now()
            thirty_days_ago = now - timedelta(days=30)
            
            low_stock_items = [i for i in inventory if i.get("status") == "low_stock"]
            out_of_stock_items = [i for i in inventory if i.get("status") == "out_of_stock"]
            total_inventory_value = sum(i.get("quantity", 0) * i.get("unit_cost", 0) for i in inventory)
            total_inventory_quantity = sum(i.get("quantity", 0) for i in inventory)
            
            metrics = {
                "total_inventory_items": len(inventory),
                "total_inventory_quantity": total_inventory_quantity,
                "low_stock_items": len(low_stock_items),
                "out_of_stock_items": len(out_of_stock_items),
                "total_inventory_value": round(total_inventory_value, 2),
            }
            
            analysis_result = analyze_inventory_data({"metrics": metrics})
            
            if not analysis_result:
                raise HTTPException(status_code=404, detail="No inventory data available")
            
            report = ReportGenerator.create_inventory_report(
                business_name=business_name,
                analysis_result=analysis_result,
                business_profile=business_profile
            )
        
        elif report_type == "revenue":
            from .analysis_tools import analyze_revenue_data
            from datetime import datetime, timedelta
            
            now = datetime.now()
            thirty_days_ago = now - timedelta(days=30)
            
            recent_orders = [o for o in orders if datetime.fromisoformat(o.get("created_at", now.isoformat())) >= thirty_days_ago]
            total_revenue_30d = sum(o.get("total_amount", 0) for o in recent_orders)
            avg_order_value = total_revenue_30d / len(recent_orders) if recent_orders else 0
            
            metrics = {
                "revenue_last_30_days": round(total_revenue_30d, 2),
                "orders_last_30_days": len(recent_orders),
                "avg_order_value": round(avg_order_value, 2),
            }
            
            analysis_result = analyze_revenue_data({"metrics": metrics})
            
            if not analysis_result:
                raise HTTPException(status_code=404, detail="No revenue data available")
            
            report = ReportGenerator.create_revenue_report(
                business_name=business_name,
                analysis_result=analysis_result,
                business_profile=business_profile
            )
        
        else:
            raise HTTPException(status_code=400, detail=f"Unknown report type: {report_type}")
        
        # Export in requested format
        if format == "json":
            return Response(
                content=report.to_json(),
                media_type="application/json",
                headers={
                    "Content-Disposition": f"attachment; filename={report_type}_report_{datetime.now().strftime('%Y%m%d')}.json"
                }
            )
        elif format == "markdown":
            return Response(
                content=report.to_markdown(),
                media_type="text/markdown",
                headers={
                    "Content-Disposition": f"attachment; filename={report_type}_report_{datetime.now().strftime('%Y%m%d')}.md"
                }
            )
        else:
            # HTML format (basic)
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>{report.title}</title>
                <style>
                    body {{ font-family: Arial, sans-serif; max-width: 1200px; margin: 40px auto; padding: 20px; }}
                    h1 {{ color: #2563eb; }}
                    h2 {{ color: #1e40af; border-bottom: 2px solid #3b82f6; padding-bottom: 10px; }}
                    .metadata {{ background: #f3f4f6; padding: 15px; border-radius: 8px; margin: 20px 0; }}
                    .section {{ margin: 30px 0; }}
                    .insights {{ background: #dbeafe; padding: 15px; border-left: 4px solid #3b82f6; }}
                    .recommendations {{ background: #d1fae5; padding: 15px; border-left: 4px solid #10b981; }}
                    ul {{ line-height: 1.8; }}
                </style>
            </head>
            <body>
                <h1>{report.title}</h1>
                <div class="metadata">
                    <p><strong>Business:</strong> {report.business_name}</p>
                    <p><strong>Report Type:</strong> {report.report_type}</p>
                    <p><strong>Generated:</strong> {report.generated_at.strftime('%Y-%m-%d %H:%M:%S')}</p>
                </div>
                
                <h2>Executive Summary</h2>
                <p>{report.summary}</p>
                
                {"".join([f'''
                <div class="section">
                    <h2>{section.title}</h2>
                    <p>{section.content}</p>
                    
                    {f'<div class="insights"><h3>Key Insights</h3><ul>{"".join([f"<li>{i}</li>" for i in section.insights])}</ul></div>' if section.insights else ''}
                    
                    {f'<div class="recommendations"><h3>Recommendations</h3><ol>{"".join([f"<li>{r}</li>" for r in section.recommendations])}</ol></div>' if section.recommendations else ''}
                </div>
                ''' for section in report.sections])}
            </body>
            </html>
            """
            return Response(
                content=html_content,
                media_type="text/html",
                headers={
                    "Content-Disposition": f"attachment; filename={report_type}_report_{datetime.now().strftime('%Y%m%d')}.html"
                }
            )
    
    except Exception as e:
        logger.error(f"Error generating report: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/v1/tenants/{tenant_id}/data/seed")
async def seed_tenant_data(tenant_id: str):
    """
    Seed tenant with sample data for testing (DEVELOPMENT ONLY)
    
    Creates realistic orders, inventory, and customer data in memory.
    This allows testing the AI coach without connecting real data sources.
    
    WARNING: This endpoint should be disabled in production!
    Data is stored in memory and will be lost on service restart.
    
    For production, use the connectors service to sync data from real sources.
    """
    try:
        now = datetime.now()
        
        # Generate realistic order data (last 90 days)
        orders = []
        for days_ago in range(90):
            date = now - timedelta(days=days_ago)
            is_weekend = date.weekday() >= 5
            daily_orders = 3 if is_weekend else 8
            
            for i in range(daily_orders):
                order_id = f"ORD-{date.strftime('%Y%m%d')}-{i+1}"
                orders.append({
                    "id": order_id,
                    "customer_id": f"cust-{(days_ago * 10 + i) % 200}",
                    "total_amount": round(120 + (i * 15) + (days_ago % 50), 2),
                    "status": "completed" if days_ago > 2 else "pending",
                    "items_count": 1 + (i % 3),
                    "created_at": date.isoformat(),
                    "product_category": ["outdoor-gear", "equipment", "accessories", "clothing"][i % 4]
                })
        
        # Generate inventory data
        inventory = []
        categories = {
            "outdoor-gear": ["Tent", "Backpack", "Sleeping Bag", "Camping Stove", "Headlamp"],
            "equipment": ["Hiking Boots", "Trekking Poles", "Water Filter", "Multi-tool", "Compass"],
            "accessories": ["Water Bottle", "First Aid Kit", "Rope", "Carabiner", "Whistle"],
            "clothing": ["Rain Jacket", "Thermal Pants", "Gloves", "Hat", "Socks"]
        }
        
        sku_id = 1
        for category, products in categories.items():
            for product in products:
                base_qty = 15
                if sku_id % 7 == 0:
                    quantity = 2
                    status = "low_stock"
                elif sku_id % 11 == 0:
                    quantity = 0
                    status = "out_of_stock"
                else:
                    quantity = base_qty + (sku_id % 20)
                    status = "in_stock"
                
                inventory.append({
                    "id": f"inv-{sku_id}",
                    "sku": f"SKU-{sku_id:04d}",
                    "product_name": product,
                    "category": category,
                    "quantity": quantity,
                    "reorder_point": 5,
                    "unit_cost": 25 + (sku_id * 3),
                    "retail_price": 50 + (sku_id * 5),
                    "status": status,
                    "supplier": f"Supplier {(sku_id % 5) + 1}"
                })
                sku_id += 1
        
        # Generate customer data
        customers = []
        for i in range(200):
            if i < 20:
                total_orders = 15 + (i % 10)
                lifetime_value = 5000 + (i * 200)
                segment = "vip"
            elif i < 80:
                total_orders = 5 + (i % 5)
                lifetime_value = 1500 + (i * 50)
                segment = "regular"
            else:
                total_orders = 1 + (i % 3)
                lifetime_value = 300 + (i * 10)
                segment = "occasional"
            
            customers.append({
                "id": f"cust-{i}",
                "name": f"Customer {i}",
                "email": f"customer{i}@example.com",
                "total_orders": total_orders,
                "lifetime_value": round(lifetime_value, 2),
                "segment": segment,
                "last_order_date": (now - timedelta(days=i % 30)).isoformat(),
                "created_at": (now - timedelta(days=180 + i)).isoformat()
            })
        
        # Store in memory (for development/testing)
        TENANT_CONNECTOR_DATA[tenant_id] = {
            "orders": orders,
            "inventory": inventory,
            "customers": customers,
            "metadata": {
                "is_sample_data": True,
                "orders_source": "Sample data (seeded for testing)",
                "inventory_source": "Sample data (seeded for testing)",
                "customers_source": "Sample data (seeded for testing)",
            },
            "_meta": {
                "generated": now.isoformat(),
                "tenant_id": tenant_id,
                "data_source": "seeded",
                "note": "Sample data generated for testing. This data is stored in memory and will be lost on service restart."
            }
        }
        
        logger.info(
            f"[seed_tenant_data] Seeded {len(orders)} orders, "
            f"{len(inventory)} inventory items, {len(customers)} customers for tenant {tenant_id} (in-memory)"
        )
        
        return {
            "success": True,
            "tenant_id": tenant_id,
            "counts": {
                "orders": len(orders),
                "inventory": len(inventory),
                "customers": len(customers)
            },
            "storage": "in-memory",
            "message": "Sample data seeded successfully. You can now test the AI coach with realistic data. Note: Data is stored in memory and will be lost on service restart."
        }
    
    except Exception as e:
        logger.error(f"[seed_tenant_data] Failed to seed data for tenant {tenant_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to seed data: {str(e)}")


# In-memory storage for generated reports (move to database in production)
TENANT_REPORTS: Dict[str, Dict[str, Any]] = {}

# In-memory storage for pending executions that paused for human review
# Keyed by review_id; values hold remaining tasks and context to resume
PENDING_EXECUTIONS: Dict[str, Dict[str, Any]] = {}


class DownloadReportRequest(BaseModel):
    report_id: str
    format: str = Field(default="html", description="Format: html, json, markdown, pdf")
    include_thinking: bool = Field(default=True, description="Include agent reasoning")
    include_evidence: bool = Field(default=True, description="Include evidence and calculations")


@app.post("/v1/tenants/{tenant_id}/reports/download")
async def download_report(tenant_id: str, request: DownloadReportRequest):
    """
    Download a generated report in various formats
    
    Supports: HTML, JSON, Markdown, PDF
    """
    logger.info(f"[download_report] 📥 Downloading report {request.report_id} for tenant {tenant_id} in format {request.format}")
    
    try:
        # Get report from storage
        if tenant_id not in TENANT_REPORTS or request.report_id not in TENANT_REPORTS[tenant_id]:
            raise HTTPException(status_code=404, detail="Report not found")
        
        report_data = TENANT_REPORTS[tenant_id][request.report_id]
        report = report_data["report"]
        
        # Generate requested format
        if request.format == "html":
            content = report.to_html(
                include_thinking=request.include_thinking,
                include_evidence=request.include_evidence
            )
            media_type = "text/html"
            filename = f"{report.title.replace(' ', '_')}_{report.report_id}.html"
        
        elif request.format == "json":
            content = report.to_json()
            media_type = "application/json"
            filename = f"{report.title.replace(' ', '_')}_{report.report_id}.json"
        
        elif request.format == "markdown":
            content = report.to_markdown()
            media_type = "text/markdown"
            filename = f"{report.title.replace(' ', '_')}_{report.report_id}.md"
        
        elif request.format == "pdf":
            # PDF generation requires additional library (weasyprint or pdfkit)
            # For now, return HTML and suggest client-side conversion
            content = report.to_html(
                include_thinking=request.include_thinking,
                include_evidence=request.include_evidence
            )
            media_type = "application/pdf"
            filename = f"{report.title.replace(' ', '_')}_{report.report_id}.pdf"
            # TODO: Add PDF generation with weasyprint
            raise HTTPException(status_code=501, detail="PDF generation coming soon. Use HTML format and print to PDF.")
        
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported format: {request.format}")
        
        logger.info(f"[download_report] ✅ Generated {request.format} report: {filename}")
        
        from fastapi.responses import Response
        
        return Response(
            content=content,
            media_type=media_type,
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"',
                "X-Report-ID": request.report_id,
                "X-Format": request.format
            }
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[download_report] Failed to generate report: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate report: {str(e)}")


class ShareReportRequest(BaseModel):
    report_id: str
    expiry_days: int = Field(default=7, description="Number of days until link expires")


@app.post("/v1/tenants/{tenant_id}/reports/share")
async def share_report(tenant_id: str, request: ShareReportRequest):
    """
    Generate a shareable link for a report
    
    Returns a public URL that expires after specified days
    """
    logger.info(f"[share_report] 🔗 Creating shareable link for report {request.report_id}")
    
    try:
        # Get report from storage
        if tenant_id not in TENANT_REPORTS or request.report_id not in TENANT_REPORTS[tenant_id]:
            raise HTTPException(status_code=404, detail="Report not found")
        
        report_data = TENANT_REPORTS[tenant_id][request.report_id]
        
        # Generate share token
        share_token = f"share-{uuid.uuid4().hex[:16]}"
        expiry_date = datetime.now() + timedelta(days=request.expiry_days)
        
        # Store share info
        if "shares" not in report_data:
            report_data["shares"] = {}
        
        report_data["shares"][share_token] = {
            "created_at": datetime.now().isoformat(),
            "expires_at": expiry_date.isoformat(),
            "views": 0
        }
        
        # Generate shareable URL
        # In production, this would be your public domain
        share_url = f"/v1/public/reports/{share_token}"
        
        logger.info(f"[share_report] ✅ Created shareable link: {share_url}")
        
        return {
            "share_url": share_url,
            "share_token": share_token,
            "expires_at": expiry_date.isoformat(),
            "report_id": request.report_id,
            "message": "Report can be accessed via this link until expiry"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[share_report] Failed to create share link: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create share link: {str(e)}")


@app.get("/v1/public/reports/{share_token}")
async def get_shared_report(share_token: str, format: str = Query(default="html")):
    """
    Access a shared report via public link
    
    No authentication required, but link must be valid and not expired
    """
    logger.info(f"[get_shared_report] 👁️ Accessing shared report: {share_token}")
    
    try:
        # Find report by share token
        for tenant_id, reports in TENANT_REPORTS.items():
            for report_id, report_data in reports.items():
                if "shares" in report_data and share_token in report_data["shares"]:
                    share_info = report_data["shares"][share_token]
                    
                    # Check expiry
                    expiry = datetime.fromisoformat(share_info["expires_at"])
                    if datetime.now() > expiry:
                        raise HTTPException(status_code=410, detail="Share link has expired")
                    
                    # Increment view count
                    share_info["views"] += 1
                    
                    # Return report
                    report = report_data["report"]
                    
                    if format == "html":
                        content = report.to_html(include_thinking=True, include_evidence=True)
                        media_type = "text/html"
                    elif format == "json":
                        content = report.to_json()
                        media_type = "application/json"
                    elif format == "markdown":
                        content = report.to_markdown()
                        media_type = "text/markdown"
                    else:
                        raise HTTPException(status_code=400, detail=f"Unsupported format: {format}")
                    
                    from fastapi.responses import Response
                    
                    return Response(
                        content=content,
                        media_type=media_type,
                        headers={
                            "X-Report-ID": report_id,
                            "X-Share-Token": share_token,
                            "X-Views": str(share_info["views"])
                        }
                    )
        
        raise HTTPException(status_code=404, detail="Share link not found or invalid")
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[get_shared_report] Failed to access shared report: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to access shared report: {str(e)}")


@app.get("/v1/tenants/{tenant_id}/reports")
async def list_reports(tenant_id: str, limit: int = Query(default=10)):
    """List all generated reports for a tenant"""
    logger.info(f"[list_reports] 📋 Listing reports for tenant {tenant_id}")
    
    try:
        if tenant_id not in TENANT_REPORTS:
            return {"reports": []}
        
        reports = []
        for report_id, report_data in list(TENANT_REPORTS[tenant_id].items())[:limit]:
            report = report_data["report"]
            reports.append({
                "report_id": report.report_id,
                "title": report.title,
                "report_type": report.report_type,
                "generated_at": report.generated_at.isoformat(),
                "query": report_data.get("original_query", ""),
                "sections_count": len(report.sections),
                "has_shares": len(report_data.get("shares", {})) > 0
            })
        
        return {"reports": reports}
    
    except Exception as e:
        logger.error(f"[list_reports] Failed to list reports: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list reports: {str(e)}")


class HumanReviewRequest(BaseModel):
    approved: bool
    feedback: Optional[str] = None
    corrections: Optional[Dict[str, Any]] = None


@app.post("/v1/tenants/{tenant_id}/task-planner/reviews/{review_id}")
async def submit_taskplanner_review(tenant_id: str, review_id: str, request: HumanReviewRequest):
    """Submit human-in-the-loop review decision for a task planner pending review.

    The response contains a summary with final_result. The orchestrator can use this
    to finalize the sub-task or re-enqueue work based on 'approved' flag.
    """
    try:
        from .task_planner import get_task_planner

        planner = get_task_planner()
        summary = planner.submit_human_review(
            review_id=review_id,
            approved=request.approved,
            feedback=request.feedback,
            corrections=request.corrections,
        )
        if summary.get("status") == "error":
            raise HTTPException(status_code=404, detail=summary.get("message", "Unknown review id"))
        # If we have a pending execution for this review, attach the decision for resume flow
        try:
            if review_id in PENDING_EXECUTIONS:
                PENDING_EXECUTIONS[review_id]["review_decision"] = summary
                logger.info(f"[submit_taskplanner_review] 📌 Stored review decision for resume (review_id={review_id})")
        except Exception as e:
            logger.warning(f"[submit_taskplanner_review] Unable to attach review decision to pending execution: {e}")
        return summary
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[submit_taskplanner_review] Failed to submit human review: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to submit human review: {str(e)}")


@app.get("/v1/tenants/{tenant_id}/task-planner/reviews")
async def list_taskplanner_pending_reviews(tenant_id: str):
    """List all pending human reviews for this tenant, enriched with resume context."""
    try:
        from .task_planner import get_task_planner
        planner = get_task_planner()
        pending = planner.list_pending_reviews()

        enriched = []
        for item in pending:
            rid = item.get("review_id")
            ctx = PENDING_EXECUTIONS.get(rid) if isinstance(rid, str) and rid else None
            enriched.append({
                **item,
                "has_pending_execution": bool(ctx),
                "awaiting_task_description": ctx.get("awaiting_task_description") if ctx else None,
                "remaining_tasks_count": len(ctx.get("remaining_tasks", [])) if ctx else 0,
                "tenant_id": tenant_id,
            })
        return {"items": enriched, "count": len(enriched)}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[list_taskplanner_pending_reviews] Failed to list pending reviews: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list pending reviews: {str(e)}")

@app.get("/v1/tenants/{tenant_id}/coach/chat/resume/{review_id}/stream")
async def resume_coach_chat_stream(tenant_id: str, review_id: str):
    """Resume a previously paused coach stream after human approval via SSE."""
    try:
        ctx = PENDING_EXECUTIONS.get(review_id)
        if not ctx:
            raise HTTPException(status_code=404, detail="Pending execution not found for this review id")
        if ctx.get("tenant_id") != tenant_id:
            raise HTTPException(status_code=403, detail="Tenant mismatch for pending execution")

        # Extract context
        remaining_tasks = ctx.get("remaining_tasks", [])
        available_data = ctx.get("available_data", {})
        business_context = ctx.get("business_context", {})
        task_results_stream = ctx.get("task_results_stream", {})
        task_planner = ctx.get("task_planner")
        run_id = ctx.get("run_id")
        request_message = ctx.get("request_message", "")
        business_name = ctx.get("business_name", "your business")
        conversation_history = ctx.get("conversation_history", [])
        awaiting_task_id = ctx.get("awaiting_task_id")
        review_decision = ctx.get("review_decision")

        # Validate required context
        if task_planner is None:
            raise HTTPException(status_code=500, detail="Pending execution missing task planner context")
        if not run_id:
            # Create a new run log if missing
            run_id = create_runlog(tenant_id, input_text=f"[resume] {request_message}", persona=None, metadata={"source": "resume_coach_chat_stream"})

        # Coach service
        coach = get_multi_agent_coach()

        # Build initial executed tasks list for report generation compatibility
        from .task_planner import SubTask, TaskStatus as PlannerTaskStatus
        executed_sub_tasks: list[SubTask] = []
        if review_decision and awaiting_task_id:
            # Apply final_result to context
            final_result = review_decision.get("final_result")
            if isinstance(final_result, dict):
                try:
                    business_context.setdefault("metrics", {}).update(final_result)
                except Exception:
                    pass
            # Save into task_results
            task_results_stream[awaiting_task_id] = final_result
            # Add as completed subtask for report building
            executed_sub_tasks.append(SubTask(
                id=awaiting_task_id,
                description=ctx.get("awaiting_task_description", awaiting_task_id),
                status=PlannerTaskStatus.COMPLETED,
                result=final_result
            ))

        async def event_generator():
            try:
                # Continue executing remaining tasks
                for task in remaining_tasks:
                    progress_msg = f"{task.description}\n"
                    yield f"data: {json.dumps({'delta': progress_msg, 'done': False, 'metadata': {'phase': 'task_execution', 'task_id': task.id}})}\n\n"

                    completed_task = task_planner.execute_task(task, available_data)

                    if completed_task.status.value == "awaiting_human":
                        logger.info(f"[resume_coach_chat_stream] ⏸ Task {task.id} awaiting human review again")
                        review_info = completed_task.result or {}
                        # Store new pending state replacing old entry
                        try:
                            _rid2 = review_info.get('review_id')
                            if _rid2:
                                # Overwrite store with new state
                                PENDING_EXECUTIONS[_rid2] = {
                                    'tenant_id': tenant_id,
                                    'awaiting_task_id': task.id,
                                    'awaiting_task_description': task.description,
                                    'remaining_tasks': remaining_tasks[remaining_tasks.index(task)+1:],
                                    'available_data': available_data,
                                    'business_context': business_context,
                                    'task_results_stream': task_results_stream,
                                    'task_planner': task_planner,
                                    'run_id': run_id,
                                    'request_message': request_message,
                                    'business_name': business_name,
                                    'conversation_history': conversation_history,
                                }
                                # Remove old review context
                                PENDING_EXECUTIONS.pop(review_id, None)
                        except Exception as store_err:
                            logger.warning(f"[resume_coach_chat_stream] Failed to store subsequent pending execution: {store_err}")

                        yield f"data: {json.dumps({'delta': '⏸ Awaiting your approval\n', 'done': False, 'metadata': {'phase': 'task_execution', 'task_id': task.id, 'task_status': 'awaiting_human', 'review_id': review_info.get('review_id'), 'proposed_result': review_info.get('proposed_result')}})}\n\n"
                        yield f"data: {json.dumps({'delta': '', 'done': True, 'metadata': {'phase': 'task_execution', 'task_id': task.id, 'task_status': 'awaiting_human'}})}\n\n"
                        return

                    if completed_task.status.value == "completed":
                        task_results_stream[task.id] = completed_task.result
                        if completed_task.result:
                            try:
                                business_context.setdefault("metrics", {}).update(completed_task.result)
                            except Exception:
                                pass
                        executed_sub_tasks.append(completed_task)
                        yield f"data: {json.dumps({'delta': '✓ ', 'done': False, 'metadata': {'phase': 'task_execution', 'task_status': 'completed'}})}\n\n"
                    else:
                        yield f"data: {json.dumps({'delta': '✗ Failed\n', 'done': False, 'metadata': {'phase': 'task_execution', 'task_status': 'failed'}})}\n\n"

                # Finished Phase 1; clear stored context
                PENDING_EXECUTIONS.pop(review_id, None)

                # Prepare sub_tasks variable for report generation block
                sub_tasks = executed_sub_tasks
                business_context["task_results"] = task_results_stream
                business_context["sub_tasks_completed"] = [t.id for t in executed_sub_tasks]

                # Report generation (same as main stream)
                logger.info(f"[resume_coach_chat_stream] 📊 Generating downloadable report...")
                try:
                    report_generator = get_report_generator()
                    from .report_generator import BusinessReport, ReportSection, AgentThought, Evidence

                    report = BusinessReport(
                        title="Business Analysis Report",
                        business_name=business_name,
                        report_type="comprehensive_analysis"
                    )

                    for task in sub_tasks:
                        if task.status.value == "completed" and task.result:
                            result = task.result
                            agent_thoughts = []
                            if "agent_thoughts" in result:
                                for thought_data in result["agent_thoughts"]:
                                    agent_thoughts.append(AgentThought(
                                        agent_name=thought_data.get("agent", "Analysis Agent"),
                                        thought=thought_data.get("thought", ""),
                                        action=thought_data.get("action", ""),
                                        observation=thought_data.get("observation", ""),
                                        data_source=thought_data.get("data_source", "")
                                    ))
                            evidence_list = []
                            if "evidence" in result:
                                for ev_data in result["evidence"]:
                                    evidence_list.append(Evidence(
                                        claim=ev_data.get("claim", ""),
                                        data_source=ev_data.get("data_source", ""),
                                        calculation=ev_data.get("calculation", ""),
                                        raw_value=ev_data.get("value", ""),
                                        confidence=ev_data.get("confidence", 1.0)
                                    ))
                            section = ReportSection(
                                title=task.description,
                                content=f"Analysis completed for: {task.description}",
                                data=result,
                                insights=[],
                                recommendations=[],
                                agent_thoughts=agent_thoughts,
                                evidence=evidence_list
                            )
                            report.add_section(section)

                    report.set_summary(f"Analyzed data for {business_name} across {len(sub_tasks)} dimensions.")

                    if tenant_id not in TENANT_REPORTS:
                        TENANT_REPORTS[tenant_id] = {}
                    TENANT_REPORTS[tenant_id][report.report_id] = {
                        "report": report,
                        "original_query": request_message,
                        "created_at": datetime.now().isoformat()
                    }

                    report_msg = f"\n📊 **Report Generated:** [Download Report](/v1/tenants/{tenant_id}/reports/download?report_id={report.report_id}&format=html) | Report ID: `{report.report_id}`\n\n"
                    yield f"data: {json.dumps({'delta': report_msg, 'done': False, 'metadata': {'phase': 'report_generated', 'report_id': report.report_id}})}\n\n"
                except Exception as report_error:
                    logger.error(f"[resume_coach_chat_stream] ⚠️ Failed to generate report: {report_error}")

                # Separator
                yield f"data: {json.dumps({'delta': '\n🤖 Analyzing results...\n\n', 'done': False, 'metadata': {'phase': 'analysis'}})}\n\n"

                # Phase 2: Coach analysis
                async for chunk in coach.stream_response(
                    tenant_id=tenant_id,
                    user_message=request_message,
                    business_context=business_context,
                    conversation_history=conversation_history
                ):
                    try:
                        if getattr(chunk, "delta", None):
                            runlog_append_output(tenant_id, run_id, getattr(chunk, "delta"))
                        meta = getattr(chunk, "metadata", {}) or {}
                        if isinstance(meta, dict) and meta.get("tool_event"):
                            runlog_append_event(tenant_id, run_id, meta["tool_event"])
                        if getattr(chunk, "done", False):
                            run_url = f"/v1/tenants/{tenant_id}/coach/runs/{run_id}"
                            runlog_finalize(tenant_id, run_id, metadata={"run_url": run_url})
                            meta = dict(meta)
                            meta.setdefault("run_url", run_url)
                            try:
                                payload = {"delta": chunk.delta, "done": True, "metadata": meta}
                                yield f"data: {json.dumps(payload)}\n\n"
                                continue
                            except Exception:
                                pass
                    except Exception:
                        pass
                    yield f"data: {chunk.model_dump_json()}\n\n"
            except Exception as e:
                logger.error(f"[resume_coach_chat_stream] ❌ Error resuming stream: {str(e)}", exc_info=True)
                error_chunk = {"delta": f"\n\nError resuming: {str(e)}", "done": True, "metadata": {"error": str(e)}}
                yield f"data: {json.dumps(error_chunk)}\n\n"

        return StreamingResponse(
            event_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[resume_coach_chat_stream] FATAL: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to resume execution: {str(e)}")


