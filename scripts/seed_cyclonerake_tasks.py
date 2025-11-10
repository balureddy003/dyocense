"""
Seed script to initialize sample tasks for CycloneRake.com demo
"""
import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from services.smb_gateway.tasks_service import get_tasks_service, CreateTaskRequest, TaskCategory, TaskPriority
from services.smb_gateway.goals_service import get_goals_service


async def seed_cyclonerake_tasks():
    """Seed sample tasks for CycloneRake tenant"""
    tasks_service = get_tasks_service()
    goals_service = get_goals_service()
    tenant_id = "tenant-demo"  # CycloneRake demo tenant
    
    # Clear existing tasks (for demo purposes)
    if tenant_id in tasks_service.tasks:
        tasks_service.tasks[tenant_id].clear()
    
    # Get existing goals to link tasks
    goals = goals_service.get_goals(tenant_id)
    goal_map = {g.title: g for g in goals}
    
    revenue_goal_id = goal_map["Seasonal Revenue Boost"].id if "Seasonal Revenue Boost" in goal_map else None
    ops_goal_id = goal_map["Inventory Optimization"].id if "Inventory Optimization" in goal_map else None
    customer_goal_id = goal_map["Customer Retention"].id if "Customer Retention" in goal_map else None
    
    # Task 1: Review abandoned carts (Sales)
    task1 = tasks_service.create_task(
        tenant_id,
        CreateTaskRequest(
            title="Review GrandNode abandoned carts",
            description="Analyze abandoned cart data from GrandNode and create recovery campaign for outdoor equipment",
            category=TaskCategory.SALES,
            priority=TaskPriority.HIGH,
            goal_id=revenue_goal_id,
            due_date="2025-11-12",
        )
    )
    print(f"✅ Created task: {task1.title} (ID: {task1.id})")
    
    # Task 2: Update inventory levels (Operations)
    task2 = tasks_service.create_task(
        tenant_id,
        CreateTaskRequest(
            title="Update Kennedy ERP inventory levels",
            description="Sync inventory data between Salesforce Kennedy ERP and GrandNode for popular rake models",
            category=TaskCategory.INVENTORY,
            priority=TaskPriority.HIGH,
            goal_id=ops_goal_id,
            due_date="2025-11-13",
        )
    )
    print(f"✅ Created task: {task2.title} (ID: {task2.id})")
    
    # Task 3: Analyze top-selling products
    task3 = tasks_service.create_task(
        tenant_id,
        CreateTaskRequest(
            title="Analyze top-selling outdoor gear",
            description="Review sales data to identify bestsellers and optimize inventory for holiday season",
            category=TaskCategory.OPERATIONS,
            priority=TaskPriority.MEDIUM,
            goal_id=revenue_goal_id,
            due_date="2025-11-15",
        )
    )
    print(f"✅ Created task: {task3.title} (ID: {task3.id})")
    
    # Task 4: Follow up with wholesale customers
    task4 = tasks_service.create_task(
        tenant_id,
        CreateTaskRequest(
            title="Follow up with wholesale customers",
            description="Reach out to B2B customers about bulk orders for spring lawn season",
            category=TaskCategory.SALES,
            priority=TaskPriority.MEDIUM,
            goal_id=customer_goal_id,
            due_date="2025-11-17",
        )
    )
    print(f"✅ Created task: {task4.title} (ID: {task4.id})")
    
    # Task 5: Optimize product recommendations
    task5 = tasks_service.create_task(
        tenant_id,
        CreateTaskRequest(
            title="Optimize product recommendations",
            description="Configure GrandNode recommendation engine based on customer purchase patterns",
            category=TaskCategory.MARKETING,
            priority=TaskPriority.MEDIUM,
            goal_id=customer_goal_id,
            due_date="2025-11-18",
        )
    )
    print(f"✅ Created task: {task5.title} (ID: {task5.id})")
    
    # Task 6: Launch email campaign
    task6 = tasks_service.create_task(
        tenant_id,
        CreateTaskRequest(
            title="Launch holiday email campaign",
            description="Create and send promotional email for Black Friday outdoor equipment sale",
            category=TaskCategory.MARKETING,
            priority=TaskPriority.HIGH,
            goal_id=revenue_goal_id,
            due_date="2025-11-20",
        )
    )
    print(f"✅ Created task: {task6.title} (ID: {task6.id})")
    
    # Display summary
    all_tasks = tasks_service.get_tasks(tenant_id)
    print(f"\n📊 Total tasks for {tenant_id}: {len(all_tasks)}")
    print("\nTasks by category:")
    for category in TaskCategory:
        category_tasks = [t for t in all_tasks if t.category == category]
        if category_tasks:
            print(f"  • {category.value}: {len(category_tasks)} tasks")


if __name__ == "__main__":
    print("🌱 Seeding CycloneRake.com demo tasks...\n")
    asyncio.run(seed_cyclonerake_tasks())
    print("\n✨ Done! Tasks are ready for the demo.")
