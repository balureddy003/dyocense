"""
Tasks Service for SMB Gateway

Manages business tasks with goal linkage and AI-powered generation
"""
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum


class TaskPriority(str, Enum):
    """Task priority levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class TaskStatus(str, Enum):
    """Task status"""
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class TaskCategory(str, Enum):
    """Task categories matching business areas"""
    SALES = "sales"
    MARKETING = "marketing"
    OPERATIONS = "operations"
    CUSTOMER_SERVICE = "customer_service"
    FINANCE = "finance"
    INVENTORY = "inventory"
    OTHER = "other"


class TaskHorizon(str, Enum):
    """Task planning horizon"""
    DAILY = "daily"
    WEEKLY = "weekly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"


class Task(BaseModel):
    """Task model"""
    id: str
    tenant_id: str
    title: str
    description: str
    category: TaskCategory
    priority: TaskPriority
    status: TaskStatus
    horizon: TaskHorizon = TaskHorizon.WEEKLY  # Planning horizon
    goal_id: Optional[str] = None  # Link to goal
    due_date: Optional[str] = None  # ISO date string
    completed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    ai_generated: bool = False
    is_starter_task: bool = False  # Flag for non-persisted starter tasks
    order: int = 0  # For sorting/ordering tasks


class CreateTaskRequest(BaseModel):
    """Request to create a new task"""
    title: str = Field(..., min_length=1, max_length=200)
    description: str = Field(default="", max_length=1000)
    category: TaskCategory
    priority: TaskPriority = TaskPriority.MEDIUM
    horizon: TaskHorizon = TaskHorizon.WEEKLY
    goal_id: Optional[str] = None
    due_date: Optional[str] = None
    ai_generated: bool = False


class UpdateTaskRequest(BaseModel):
    """Request to update a task"""
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    category: Optional[TaskCategory] = None
    priority: Optional[TaskPriority] = None
    status: Optional[TaskStatus] = None
    horizon: Optional[TaskHorizon] = None
    goal_id: Optional[str] = None
    due_date: Optional[str] = None
    order: Optional[int] = None


class TasksService:
    """Service for managing tasks"""
    
    def __init__(self):
        # In-memory storage (replace with database in production)
        self.tasks: Dict[str, Dict[str, Task]] = {}  # {tenant_id: {task_id: Task}}
    
    def create_task(self, tenant_id: str, request: CreateTaskRequest) -> Task:
        """Create a new task"""
        import uuid
        
        task_id = f"task-{uuid.uuid4().hex[:12]}"
        now = datetime.now()
        
        task = Task(
            id=task_id,
            tenant_id=tenant_id,
            title=request.title,
            description=request.description,
            category=request.category,
            priority=request.priority,
            status=TaskStatus.TODO,
            goal_id=request.goal_id,
            due_date=request.due_date,
            created_at=now,
            updated_at=now,
            ai_generated=request.ai_generated,
            order=len(self.get_tasks(tenant_id, status=TaskStatus.TODO)),
        )
        
        if tenant_id not in self.tasks:
            self.tasks[tenant_id] = {}
        
        self.tasks[tenant_id][task_id] = task
        return task
    
    def get_tasks(
        self, 
        tenant_id: str, 
        status: Optional[TaskStatus] = None,
        horizon: Optional[TaskHorizon] = None,
        goal_id: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> List[Task]:
        """Get tasks for a tenant with optional filters"""
        if tenant_id not in self.tasks:
            # Generate helpful starter tasks if tenant has none
            return self._get_starter_tasks(tenant_id, horizon, limit)
        
        tenant_tasks = list(self.tasks[tenant_id].values())
        
        # Apply filters
        if status:
            tenant_tasks = [t for t in tenant_tasks if t.status == status]
        
        if horizon:
            tenant_tasks = [t for t in tenant_tasks if t.horizon == horizon]
        
        if goal_id:
            tenant_tasks = [t for t in tenant_tasks if t.goal_id == goal_id]
        
        # If no tasks match, return starter tasks
        if not tenant_tasks and status == TaskStatus.TODO:
            return self._get_starter_tasks(tenant_id, horizon, limit)
        
        # Sort by order, then by created_at descending
        tenant_tasks.sort(key=lambda t: (t.order, t.created_at), reverse=False)
        
        if limit:
            tenant_tasks = tenant_tasks[:limit]
        
        return tenant_tasks
    
    def _get_starter_tasks(self, tenant_id: str, horizon: Optional[TaskHorizon] = None, limit: Optional[int] = None) -> List[Task]:
        """Generate helpful starter tasks based on business data and planning horizon"""
        
        # Define starter tasks for each horizon
        all_starter_tasks = {
            TaskHorizon.DAILY: [
                {
                    'id': f'starter-{tenant_id}-daily-1',
                    'title': 'Review and respond to customer emails',
                    'description': 'Check customer service inbox and respond to urgent inquiries',
                    'category': TaskCategory.CUSTOMER_SERVICE,
                    'priority': TaskPriority.HIGH,
                    'due_days': 0,  # Today
                },
                {
                    'id': f'starter-{tenant_id}-daily-2',
                    'title': 'Check inventory levels for best sellers',
                    'description': 'Monitor stock levels of top-selling products to avoid stockouts',
                    'category': TaskCategory.INVENTORY,
                    'priority': TaskPriority.MEDIUM,
                    'due_days': 0,
                },
                {
                    'id': f'starter-{tenant_id}-daily-3',
                    'title': 'Review today\'s sales and metrics',
                    'description': 'Check dashboard for revenue, orders, and key performance indicators',
                    'category': TaskCategory.SALES,
                    'priority': TaskPriority.MEDIUM,
                    'due_days': 0,
                },
            ],
            TaskHorizon.WEEKLY: [
                {
                    'id': f'starter-{tenant_id}-weekly-1',
                    'title': 'Review low-stock inventory items',
                    'description': 'Check which products are running low and need reordering to avoid stockouts',
                    'category': TaskCategory.INVENTORY,
                    'priority': TaskPriority.HIGH,
                    'due_days': 7,
                },
                {
                    'id': f'starter-{tenant_id}-weekly-2',
                    'title': 'Follow up with top 5 VIP customers',
                    'description': 'Reach out to your highest-value customers to strengthen relationships and gather feedback',
                    'category': TaskCategory.CUSTOMER_SERVICE,
                    'priority': TaskPriority.MEDIUM,
                    'due_days': 7,
                },
                {
                    'id': f'starter-{tenant_id}-weekly-3',
                    'title': 'Analyze sales trends from last 30 days',
                    'description': 'Review your recent sales data to identify patterns, best sellers, and opportunities',
                    'category': TaskCategory.SALES,
                    'priority': TaskPriority.MEDIUM,
                    'due_days': 7,
                },
                {
                    'id': f'starter-{tenant_id}-weekly-4',
                    'title': 'Update product descriptions and images',
                    'description': 'Improve your e-commerce listings with better descriptions and high-quality photos',
                    'category': TaskCategory.MARKETING,
                    'priority': TaskPriority.LOW,
                    'due_days': 7,
                },
            ],
            TaskHorizon.QUARTERLY: [
                {
                    'id': f'starter-{tenant_id}-quarterly-1',
                    'title': 'Review Q4 revenue goals and strategy',
                    'description': 'Assess progress towards quarterly targets and adjust strategy if needed',
                    'category': TaskCategory.FINANCE,
                    'priority': TaskPriority.HIGH,
                    'due_days': 90,
                },
                {
                    'id': f'starter-{tenant_id}-quarterly-2',
                    'title': 'Optimize top 10 product listings',
                    'description': 'Improve SEO, images, and descriptions for your best-selling products',
                    'category': TaskCategory.MARKETING,
                    'priority': TaskPriority.MEDIUM,
                    'due_days': 90,
                },
                {
                    'id': f'starter-{tenant_id}-quarterly-3',
                    'title': 'Implement customer retention program',
                    'description': 'Launch loyalty rewards or email campaigns to improve repeat purchase rate',
                    'category': TaskCategory.MARKETING,
                    'priority': TaskPriority.MEDIUM,
                    'due_days': 90,
                },
                {
                    'id': f'starter-{tenant_id}-quarterly-4',
                    'title': 'Negotiate better supplier terms',
                    'description': 'Review supplier contracts and negotiate volume discounts or better payment terms',
                    'category': TaskCategory.OPERATIONS,
                    'priority': TaskPriority.MEDIUM,
                    'due_days': 90,
                },
            ],
            TaskHorizon.YEARLY: [
                {
                    'id': f'starter-{tenant_id}-yearly-1',
                    'title': 'Define annual revenue and growth targets',
                    'description': 'Set clear financial goals for the year including revenue, profit margins, and growth rate',
                    'category': TaskCategory.FINANCE,
                    'priority': TaskPriority.URGENT,
                    'due_days': 365,
                },
                {
                    'id': f'starter-{tenant_id}-yearly-2',
                    'title': 'Evaluate and optimize supplier relationships',
                    'description': 'Review all suppliers, consolidate where possible, and build strategic partnerships',
                    'category': TaskCategory.OPERATIONS,
                    'priority': TaskPriority.HIGH,
                    'due_days': 365,
                },
                {
                    'id': f'starter-{tenant_id}-yearly-3',
                    'title': 'Expand product line or enter new market',
                    'description': 'Research and plan for product expansion or market entry to drive growth',
                    'category': TaskCategory.OTHER,
                    'priority': TaskPriority.HIGH,
                    'due_days': 365,
                },
                {
                    'id': f'starter-{tenant_id}-yearly-4',
                    'title': 'Invest in business automation',
                    'description': 'Identify manual processes to automate for efficiency (inventory, orders, marketing)',
                    'category': TaskCategory.OPERATIONS,
                    'priority': TaskPriority.MEDIUM,
                    'due_days': 365,
                },
            ],
        }
        
        # Get tasks for the specified horizon, or all if not specified
        if horizon:
            task_templates = all_starter_tasks.get(horizon, [])
        else:
            # If no horizon specified, return weekly tasks as default
            task_templates = all_starter_tasks.get(TaskHorizon.WEEKLY, [])
        
        # Create Task objects (these are temporary/suggested, not persisted)
        tasks = []
        now = datetime.now()
        
        for task_data in task_templates[:limit] if limit else task_templates:
            task = Task(
                id=task_data['id'],
                tenant_id=tenant_id,
                title=task_data['title'],
                description=task_data['description'],
                category=task_data['category'],
                priority=task_data['priority'],
                status=TaskStatus.TODO,
                horizon=horizon or TaskHorizon.WEEKLY,
                goal_id=None,
                due_date=(now + timedelta(days=task_data['due_days'])).strftime('%Y-%m-%d'),
                created_at=now,
                updated_at=now,
                order=len(tasks),
                ai_generated=True,
                is_starter_task=True,  # Mark as starter task
            )
            tasks.append(task)
        
        return tasks
    
    def get_task(self, tenant_id: str, task_id: str) -> Optional[Task]:
        """Get a specific task"""
        if tenant_id not in self.tasks:
            return None
        
        return self.tasks[tenant_id].get(task_id)
    
    def update_task(self, tenant_id: str, task_id: str, request: UpdateTaskRequest) -> Optional[Task]:
        """Update a task"""
        task = self.get_task(tenant_id, task_id)
        if not task:
            return None
        
        # Update fields
        update_data = request.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(task, field, value)
        
        task.updated_at = datetime.now()
        
        # Track completion time
        if update_data.get('status') == TaskStatus.COMPLETED and not task.completed_at:
            task.completed_at = datetime.now()
        
        self.tasks[tenant_id][task_id] = task
        return task
    
    def delete_task(self, tenant_id: str, task_id: str) -> bool:
        """Delete a task"""
        if tenant_id not in self.tasks:
            return False
        
        if task_id in self.tasks[tenant_id]:
            del self.tasks[tenant_id][task_id]
            return True
        
        return False
    
    def generate_tasks_from_goal(self, tenant_id: str, goal_data: Dict[str, Any]) -> List[Task]:
        """
        AI-powered task generation from a goal
        
        For now, uses rule-based logic. In production, this would call an LLM.
        """
        generated_tasks = []
        goal_id = goal_data.get('id')
        goal_title = goal_data.get('title', '')
        goal_category = goal_data.get('category', 'custom')
        
        # Rule-based task generation based on goal category
        if goal_category == 'revenue':
            task_templates = [
                {
                    'title': f'Review current revenue metrics for "{goal_title}"',
                    'description': 'Analyze current revenue performance and identify gaps',
                    'category': TaskCategory.FINANCE,
                    'priority': TaskPriority.HIGH,
                },
                {
                    'title': 'Launch promotional campaign',
                    'description': 'Create and execute marketing campaign to drive revenue',
                    'category': TaskCategory.MARKETING,
                    'priority': TaskPriority.HIGH,
                },
                {
                    'title': 'Optimize pricing strategy',
                    'description': 'Review and adjust pricing to maximize revenue',
                    'category': TaskCategory.SALES,
                    'priority': TaskPriority.MEDIUM,
                },
            ]
        elif goal_category == 'operations':
            task_templates = [
                {
                    'title': f'Audit inventory for "{goal_title}"',
                    'description': 'Review stock levels and identify optimization opportunities',
                    'category': TaskCategory.INVENTORY,
                    'priority': TaskPriority.HIGH,
                },
                {
                    'title': 'Streamline fulfillment process',
                    'description': 'Identify and eliminate bottlenecks in operations',
                    'category': TaskCategory.OPERATIONS,
                    'priority': TaskPriority.MEDIUM,
                },
            ]
        elif goal_category == 'customer':
            task_templates = [
                {
                    'title': f'Analyze customer feedback for "{goal_title}"',
                    'description': 'Review customer reviews and support tickets',
                    'category': TaskCategory.CUSTOMER_SERVICE,
                    'priority': TaskPriority.HIGH,
                },
                {
                    'title': 'Launch customer loyalty program',
                    'description': 'Design and implement retention initiatives',
                    'category': TaskCategory.MARKETING,
                    'priority': TaskPriority.HIGH,
                },
            ]
        else:
            task_templates = [
                {
                    'title': f'Plan action items for "{goal_title}"',
                    'description': 'Break down goal into actionable steps',
                    'category': TaskCategory.OTHER,
                    'priority': TaskPriority.MEDIUM,
                },
            ]
        
        # Create tasks from templates
        for i, template in enumerate(task_templates):
            due_date = (datetime.now() + timedelta(days=7 * (i + 1))).strftime('%Y-%m-%d')
            
            task = self.create_task(
                tenant_id,
                CreateTaskRequest(
                    title=template['title'],
                    description=template['description'],
                    category=template['category'],
                    priority=template['priority'],
                    goal_id=goal_id,
                    due_date=due_date,
                    ai_generated=True,
                )
            )
            generated_tasks.append(task)
        
        return generated_tasks


# Global instance
_tasks_service = None

def get_tasks_service() -> TasksService:
    """Get tasks service instance"""
    global _tasks_service
    if _tasks_service is None:
        _tasks_service = TasksService()
    return _tasks_service
