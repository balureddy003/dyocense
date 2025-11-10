from __future__ import annotations

import uuid
from importlib import resources
import json
from typing import Dict, List, Optional
from datetime import datetime, timedelta

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
    TaskHorizon,
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
from .multi_agent_coach import (
    get_multi_agent_coach,
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
    For now, check if we have mock data, otherwise return realistic sample data
    """
    if tenant_id in TENANT_CONNECTOR_DATA:
        return TENANT_CONNECTOR_DATA[tenant_id]
    
    # Generate realistic sample data based on tenant
    # In production, this would call connector service APIs to get synced data
    now = datetime.now()
    
    # Create realistic order data with trends
    orders = []
    for days_ago in range(90):  # Last 90 days
        date = now - timedelta(days=days_ago)
        # More orders on weekdays, fewer on weekends
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
    
    # Realistic inventory with some low-stock items
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
            # Vary quantity - some items low/out of stock
            base_qty = 15
            if sku_id % 7 == 0:  # ~14% low stock
                quantity = 2
                status = "low_stock"
            elif sku_id % 11 == 0:  # ~9% out of stock
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
    
    # Realistic customer data with engagement levels
    customers = []
    for i in range(200):
        # Create customer segments
        if i < 20:  # VIP customers (10%)
            total_orders = 15 + (i % 10)
            lifetime_value = 5000 + (i * 200)
            segment = "vip"
        elif i < 80:  # Regular customers (30%)
            total_orders = 5 + (i % 5)
            lifetime_value = 1500 + (i * 50)
            segment = "regular"
        else:  # Occasional customers (60%)
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
    
    return {
        "orders": orders,
        "inventory": inventory,
        "customers": customers,
        "_meta": {
            "generated": now.isoformat(),
            "tenant_id": tenant_id,
            "data_source": "sample" ,  # Mark as sample data
            "note": "This is sample data. Connect real data sources for accurate insights."
        }
    }


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
    has_real_data = tenant_id in TENANT_CONNECTOR_DATA
    
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
            "metrics": {
                "revenue_last_30_days": round(total_revenue_30d, 2),
                "orders_last_30_days": len(recent_orders),
                "avg_order_value": round(avg_order_value, 2),
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


@app.post("/v1/tenants/{tenant_id}/coach/chat/stream")
async def coach_chat_stream(tenant_id: str, request: ChatRequest):
    """Stream conversational AI coach responses via Server-Sent Events with multi-agent orchestration"""
    # Use multi-agent coach for specialized queries
    coach = get_multi_agent_coach()
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
            "metrics": {
                "revenue_last_30_days": round(total_revenue_30d, 2),
                "orders_last_30_days": len(recent_orders),
                "avg_order_value": round(avg_order_value, 2),
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


# ===================================
# Connector Marketplace Endpoints
# ===================================

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


