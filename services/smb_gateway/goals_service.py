"""
Goals Service for SMB Gateway

Manages business goals with persistence and progress tracking
"""
from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum


class GoalCategory(str, Enum):
    """Goal category types"""
    REVENUE = "revenue"
    OPERATIONS = "operations"
    CUSTOMER = "customer"
    GROWTH = "growth"
    CUSTOM = "custom"


class GoalStatus(str, Enum):
    """Goal status"""
    ACTIVE = "active"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class Goal(BaseModel):
    """Goal model"""
    id: str
    tenant_id: str
    title: str
    description: str
    current: float
    target: float
    unit: str
    category: GoalCategory
    status: GoalStatus = GoalStatus.ACTIVE
    deadline: str  # ISO date string
    created_at: datetime
    updated_at: datetime
    auto_tracked: bool = False
    connector_source: Optional[str] = None
    last_celebrated_milestone: Optional[int] = None  # Track which milestones celebrated (25, 50, 75, 100)


class CreateGoalRequest(BaseModel):
    """Request to create a new goal"""
    title: str = Field(..., min_length=1, max_length=200)
    description: str = Field(..., max_length=1000)
    current: float = Field(default=0, ge=0)
    target: float = Field(..., gt=0)
    unit: str = Field(..., min_length=1, max_length=50)
    category: GoalCategory
    deadline: str  # ISO date string YYYY-MM-DD
    auto_tracked: bool = Field(default=False)
    connector_source: Optional[str] = None


class UpdateGoalRequest(BaseModel):
    """Request to update a goal"""
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    current: Optional[float] = Field(None, ge=0)
    target: Optional[float] = Field(None, gt=0)
    unit: Optional[str] = None
    category: Optional[GoalCategory] = None
    status: Optional[GoalStatus] = None
    deadline: Optional[str] = None
    auto_tracked: Optional[bool] = None
    connector_source: Optional[str] = None


class GoalsService:
    """Service for managing goals"""
    
    def __init__(self):
        # In-memory storage (replace with database in production)
        self.goals: Dict[str, Dict[str, Goal]] = {}  # {tenant_id: {goal_id: Goal}}
    
    def create_goal(self, tenant_id: str, request: CreateGoalRequest) -> Goal:
        """Create a new goal"""
        import uuid
        
        goal_id = f"goal-{uuid.uuid4().hex[:12]}"
        now = datetime.now()
        
        goal = Goal(
            id=goal_id,
            tenant_id=tenant_id,
            title=request.title,
            description=request.description,
            current=request.current,
            target=request.target,
            unit=request.unit,
            category=request.category,
            deadline=request.deadline,
            created_at=now,
            updated_at=now,
            auto_tracked=request.auto_tracked,
            connector_source=request.connector_source,
        )
        
        if tenant_id not in self.goals:
            self.goals[tenant_id] = {}
        
        self.goals[tenant_id][goal_id] = goal
        return goal
    
    def get_goals(self, tenant_id: str, status: Optional[GoalStatus] = None) -> List[Goal]:
        """Get all goals for a tenant"""
        if tenant_id not in self.goals:
            return []
        
        tenant_goals = list(self.goals[tenant_id].values())
        
        if status:
            tenant_goals = [g for g in tenant_goals if g.status == status]
        
        # Sort by created_at descending
        tenant_goals.sort(key=lambda g: g.created_at, reverse=True)
        
        return tenant_goals
    
    def get_goal(self, tenant_id: str, goal_id: str) -> Optional[Goal]:
        """Get a specific goal"""
        if tenant_id not in self.goals:
            return None
        
        return self.goals[tenant_id].get(goal_id)
    
    def update_goal(self, tenant_id: str, goal_id: str, request: UpdateGoalRequest) -> Optional[Goal]:
        """Update a goal"""
        goal = self.get_goal(tenant_id, goal_id)
        if not goal:
            return None
        
        # Update fields
        update_data = request.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(goal, field, value)
        
        goal.updated_at = datetime.now()
        
        # Check if goal is completed
        if goal.current >= goal.target and goal.status == GoalStatus.ACTIVE:
            goal.status = GoalStatus.COMPLETED
        
        self.goals[tenant_id][goal_id] = goal
        return goal
    
    def delete_goal(self, tenant_id: str, goal_id: str) -> bool:
        """Delete a goal"""
        if tenant_id not in self.goals:
            return False
        
        if goal_id in self.goals[tenant_id]:
            del self.goals[tenant_id][goal_id]
            return True
        
        return False
    
    async def update_auto_tracked_goals(self, tenant_id: str, connector_data: Dict[str, Any]) -> List[Goal]:
        """
        Update auto-tracked goals from connector data
        
        For example:
        - Revenue goals -> calculate from order totals
        - Inventory goals -> calculate from inventory turnover
        - Customer goals -> calculate from customer metrics
        """
        updated_goals = []
        
        tenant_goals = self.get_goals(tenant_id, status=GoalStatus.ACTIVE)
        auto_tracked = [g for g in tenant_goals if g.auto_tracked]
        
        for goal in auto_tracked:
            current_value = self._calculate_goal_progress(goal, connector_data)
            if current_value is not None and current_value != goal.current:
                goal.current = current_value
                goal.updated_at = datetime.now()
                
                # Check for completion
                if goal.current >= goal.target:
                    goal.status = GoalStatus.COMPLETED
                
                self.goals[tenant_id][goal.id] = goal
                updated_goals.append(goal)
        
        return updated_goals
    
    def _calculate_goal_progress(self, goal: Goal, connector_data: Dict[str, Any]) -> Optional[float]:
        """Calculate current progress for auto-tracked goal"""
        if goal.category == GoalCategory.REVENUE:
            # Calculate revenue from orders
            orders = connector_data.get('orders', [])
            total_revenue = sum(order.get('total_amount', 0) for order in orders)
            return total_revenue
        
        elif goal.category == GoalCategory.CUSTOMER:
            # Calculate customer metrics
            customers = connector_data.get('customers', [])
            orders = connector_data.get('orders', [])
            
            if 'repeat' in goal.title.lower():
                # Count repeat customers
                customer_order_counts = {}
                for order in orders:
                    customer_id = order.get('customer_id')
                    if customer_id:
                        customer_order_counts[customer_id] = customer_order_counts.get(customer_id, 0) + 1
                
                repeat_customers = sum(1 for count in customer_order_counts.values() if count > 1)
                return float(repeat_customers)
            else:
                # Total customers
                return float(len(customers))
        
        elif goal.category == GoalCategory.OPERATIONS:
            # Calculate operational metrics
            inventory = connector_data.get('inventory', [])
            
            if 'turnover' in goal.title.lower():
                # Calculate inventory turnover rate
                total_inventory_value = sum(item.get('value', 0) for item in inventory)
                orders = connector_data.get('orders', [])
                total_sales = sum(order.get('total_amount', 0) for order in orders)
                
                if total_inventory_value > 0:
                    turnover_rate = (total_sales * 12) / total_inventory_value  # Annualized
                    return turnover_rate
        
        return None


# Global instance
_goals_service = None

def get_goals_service() -> GoalsService:
    """Get goals service instance"""
    global _goals_service
    if _goals_service is None:
        _goals_service = GoalsService()
    return _goals_service
