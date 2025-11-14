"""
Optimization Routes

Mathematical optimization for inventory, staffing, and budgets.
"""

from __future__ import annotations

from typing import Any
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field

from backend.services.optimizer import (
    get_inventory_optimizer,
    get_staffing_optimizer,
    InventoryOptimizer,
    StaffingOptimizer
)
from backend.dependencies import get_current_user

router = APIRouter()


# --- Inventory Optimization Models ---

class EOQRequest(BaseModel):
    """Economic Order Quantity request"""
    annual_demand: float = Field(..., gt=0, description="Annual demand in units")
    order_cost: float = Field(..., gt=0, description="Cost per order ($)")
    holding_cost_per_unit: float = Field(..., gt=0, description="Annual holding cost per unit ($)")


class SafetyStockRequest(BaseModel):
    """Safety stock calculation request"""
    avg_daily_demand: float = Field(..., gt=0, description="Average daily demand")
    demand_std_dev: float = Field(..., gt=0, description="Standard deviation of daily demand")
    lead_time_days: float = Field(..., gt=0, description="Lead time in days")
    service_level: float = Field(0.95, ge=0.5, le=0.99, description="Target service level")


class ReorderPointRequest(BaseModel):
    """Reorder point with variable lead time"""
    avg_daily_demand: float = Field(..., gt=0)
    demand_std_dev: float = Field(..., gt=0)
    lead_time_days: float = Field(..., gt=0)
    lead_time_std_dev: float = Field(..., ge=0)
    service_level: float = Field(0.95, ge=0.5, le=0.99)


class MultiProductRequest(BaseModel):
    """Multi-product inventory optimization"""
    products: list[dict[str, Any]] = Field(..., description="List of products with demand, costs, etc.")
    budget_constraint: float = Field(..., gt=0, description="Max budget ($)")
    storage_constraint: float = Field(..., gt=0, description="Max storage space (sq ft)")


# --- Staffing Optimization Models ---

class ShiftScheduleRequest(BaseModel):
    """Shift scheduling request"""
    employees: list[dict[str, Any]] = Field(..., description="Employee details")
    shifts: list[dict[str, Any]] = Field(..., description="Shift definitions")
    min_coverage: dict[str, int] = Field(..., description="Min employees per shift")
    max_hours_per_week: int = Field(40, gt=0)
    planning_horizon_days: int = Field(7, gt=0)


class TaskAssignmentRequest(BaseModel):
    """Task assignment request"""
    employees: list[dict[str, Any]] = Field(..., description="Employee details")
    tasks: list[dict[str, Any]] = Field(..., description="Task definitions")
    max_tasks_per_employee: int = Field(10, gt=0)


class LaborCostRequest(BaseModel):
    """Labor cost calculation request"""
    assignments: list[dict[str, Any]] = Field(..., description="Shift assignments")
    overtime_threshold_hours: float = Field(40, gt=0)
    overtime_multiplier: float = Field(1.5, gt=1.0)


# --- Inventory Routes ---

@router.post("/inventory/eoq", response_model=dict[str, Any])
async def calculate_eoq(
    request: EOQRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Calculate Economic Order Quantity (EOQ).
    
    Determines the optimal order quantity that minimizes total inventory costs.
    """
    try:
        optimizer = get_inventory_optimizer()
        result = optimizer.calculate_eoq(
            annual_demand=request.annual_demand,
            order_cost=request.order_cost,
            holding_cost_per_unit=request.holding_cost_per_unit
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Optimization failed: {str(e)}")


@router.post("/inventory/safety-stock", response_model=dict[str, Any])
async def calculate_safety_stock(
    request: SafetyStockRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Calculate safety stock for given service level.
    
    Determines buffer inventory to maintain during lead time.
    """
    try:
        optimizer = get_inventory_optimizer()
        result = optimizer.calculate_safety_stock(
            avg_daily_demand=request.avg_daily_demand,
            demand_std_dev=request.demand_std_dev,
            lead_time_days=request.lead_time_days,
            service_level=request.service_level
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Calculation failed: {str(e)}")


@router.post("/inventory/reorder-point", response_model=dict[str, Any])
async def calculate_reorder_point(
    request: ReorderPointRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Calculate optimal reorder point with variable lead time.
    
    Accounts for uncertainty in both demand and lead time.
    """
    try:
        optimizer = get_inventory_optimizer()
        result = optimizer.optimize_reorder_point(
            avg_daily_demand=request.avg_daily_demand,
            demand_std_dev=request.demand_std_dev,
            lead_time_days=request.lead_time_days,
            lead_time_std_dev=request.lead_time_std_dev,
            service_level=request.service_level
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Optimization failed: {str(e)}")


@router.post("/inventory/multi-product", response_model=dict[str, Any])
async def optimize_multi_product(
    request: MultiProductRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Optimize inventory for multiple products with constraints.
    
    Minimizes total cost while satisfying budget and storage constraints.
    """
    try:
        optimizer = get_inventory_optimizer()
        result = optimizer.optimize_multi_product(
            products=request.products,
            budget_constraint=request.budget_constraint,
            storage_constraint=request.storage_constraint
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Optimization failed: {str(e)}")


# --- Staffing Routes ---

@router.post("/staffing/schedule", response_model=dict[str, Any])
async def optimize_shift_schedule(
    request: ShiftScheduleRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Optimize shift scheduling to minimize labor cost.
    
    Creates employee shift assignments that meet coverage requirements
    while minimizing total labor cost.
    """
    try:
        optimizer = get_staffing_optimizer()
        result = optimizer.optimize_shift_schedule(
            employees=request.employees,
            shifts=request.shifts,
            min_coverage=request.min_coverage,
            max_hours_per_week=request.max_hours_per_week,
            planning_horizon_days=request.planning_horizon_days
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Optimization failed: {str(e)}")


@router.post("/staffing/assign-tasks", response_model=dict[str, Any])
async def optimize_task_assignment(
    request: TaskAssignmentRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Assign employees to tasks to maximize total value.
    
    Optimally assigns tasks to employees based on skills and capacity.
    """
    try:
        optimizer = get_staffing_optimizer()
        result = optimizer.optimize_employee_assignment(
            employees=request.employees,
            tasks=request.tasks,
            max_tasks_per_employee=request.max_tasks_per_employee
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Optimization failed: {str(e)}")


@router.post("/staffing/labor-cost", response_model=dict[str, Any])
async def calculate_labor_cost(
    request: LaborCostRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Calculate total labor cost including overtime.
    
    Computes regular and overtime costs for shift assignments.
    """
    try:
        optimizer = get_staffing_optimizer()
        result = optimizer.calculate_labor_cost(
            assignments=request.assignments,
            overtime_threshold_hours=request.overtime_threshold_hours,
            overtime_multiplier=request.overtime_multiplier
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Calculation failed: {str(e)}")
