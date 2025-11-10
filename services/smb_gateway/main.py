from __future__ import annotations

import uuid
from importlib import resources
import json
from typing import Dict, List, Optional
from datetime import datetime

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
import jsonschema

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
)
from .coach_service import (
    get_coach_service,
    ChatRequest,
    ChatResponse,
    ChatMessage,
)
from .conversational_coach import (
    get_conversational_coach,
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
    Fetch data from connectors (GrandNode, Salesforce, etc.)
    
    TODO: Replace with actual connector service integration
    For now, check if we have mock data, otherwise return sample data
    """
    if tenant_id in TENANT_CONNECTOR_DATA:
        return TENANT_CONNECTOR_DATA[tenant_id]
    
    # Sample data for CycloneRake (outdoor equipment business)
    # This should be replaced with actual connector API calls
    now = datetime.now().isoformat()
    sample_data = {
        "orders": [
            # Current period orders (last 30 days)
            {"id": f"ord-{i}", "customer_id": f"cust-{i % 50}", "total_amount": 150 + (i * 10), "created_at": now}
            for i in range(100)
        ] + [
            # Previous period orders (30-60 days ago)
            {"id": f"ord-prev-{i}", "customer_id": f"cust-{i % 40}", "total_amount": 140 + (i * 10), "created_at": (datetime.now().replace(day=1) if datetime.now().day > 1 else datetime.now()).isoformat()}
            for i in range(80)
        ],
        "inventory": [
            {"id": f"inv-{i}", "sku": f"SKU-{i}", "quantity": 10 + (i % 20), "value": 50 + (i * 5)}
            for i in range(50)
        ] + [
            # Some stockout items
            {"id": f"inv-stockout-{i}", "sku": f"SKU-SO-{i}", "quantity": 0, "value": 100}
            for i in range(3)
        ],
        "customers": [
            {"id": f"cust-{i}", "name": f"Customer {i}", "email": f"customer{i}@example.com"}
            for i in range(150)
        ]
    }
    
    return sample_data


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
    goal_id: Optional[str] = Query(None),
    limit: Optional[int] = Query(None),
):
    """Get all tasks for the tenant with optional filters"""
    tasks_service = get_tasks_service()
    tasks = tasks_service.get_tasks(tenant_id, status=status, goal_id=goal_id, limit=limit)
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
        has_real_data = tenant_id in TENANT_CONNECTOR_DATA
        
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
        
        # Build context
        business_context = {
            "business_name": business_name,
            "industry": "retail",  # Generic industry
            "has_data_connected": has_data_connected,
            "data_sources": {
                "orders": total_orders,
                "inventory": total_inventory,
                "customers": total_customers,
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


@app.post("/v1/tenants/{tenant_id}/coach/chat/stream")
async def coach_chat_stream(tenant_id: str, request: ChatRequest):
    """Stream conversational AI coach responses via Server-Sent Events"""
    coach = get_conversational_coach()
    goals_service = get_goals_service()
    tasks_service = get_tasks_service()
    settings_service = get_settings_service()
    
    # Gather business context (same as regular coach endpoint)
    try:
        # Get connector data and check if it's real or sample data
        connector_data = await _fetch_connector_data(tenant_id)
        has_real_data = tenant_id in TENANT_CONNECTOR_DATA
        
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
        
        # Build context
        business_context = {
            "business_name": business_name,
            "industry": "retail",
            "has_data_connected": has_data_connected,
            "data_sources": {
                "orders": total_orders,
                "inventory": total_inventory,
                "customers": total_customers,
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
        
        # Create event generator for SSE streaming
        async def event_generator():
            try:
                async for chunk in coach.stream_response(
                    tenant_id=tenant_id,
                    user_message=request.message,
                    business_context=business_context,
                    conversation_history=request.conversation_history or []
                ):
                    # Format as SSE event
                    yield f"data: {chunk.model_dump_json()}\n\n"
            except Exception as e:
                # Send error as final chunk
                error_chunk = {
                    "delta": f"\n\nI apologize, but I encountered an error: {str(e)}",
                    "done": True,
                    "metadata": {"error": str(e)}
                }
                yield f"data: {json.dumps(error_chunk)}\n\n"
        
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
        raise HTTPException(status_code=500, detail=f"Coach streaming error: {str(e)}")


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
        health_score.score,
        {
            'revenue': health_score.breakdown.revenue,
            'operations': health_score.breakdown.operations,
            'customer': health_score.breakdown.customer,
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

