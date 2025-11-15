"""
Seed script to initialize sample goals for CycloneRake.com demo
"""
import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from services.smb_gateway.goals_service import get_goals_service, CreateGoalRequest, GoalCategory


async def seed_cyclonerake_goals():
    """Seed sample goals for CycloneRake tenant"""
    goals_service = get_goals_service()
    tenant_id = "tenant-demo"  # CycloneRake demo tenant
    
    # Clear existing goals (for demo purposes)
    if tenant_id in goals_service.goals:
        goals_service.goals[tenant_id].clear()
    
    # Goal 1: Seasonal Revenue Boost
    goal1 = goals_service.create_goal(
        tenant_id,
        CreateGoalRequest(
            title="Seasonal Revenue Boost",
            description="Increase Q4 revenue by 25% through holiday promotions and new product launches for outdoor equipment",
            current=78500,
            target=100000,
            unit="USD",
            category=GoalCategory.REVENUE,
            deadline="2025-12-01",
            auto_tracked=True,
            connector_source="GrandNode",
        )
    )
    print(f"✅ Created goal: {goal1.title} (ID: {goal1.id})")
    
    # Goal 2: Inventory Optimization
    goal2 = goals_service.create_goal(
        tenant_id,
        CreateGoalRequest(
            title="Inventory Optimization",
            description="Improve inventory turnover rate to reduce holding costs and prevent stockouts on popular rake models",
            current=87,
            target=95,
            unit="% Turnover",
            category=GoalCategory.OPERATIONS,
            deadline="2025-12-10",
            auto_tracked=True,
            connector_source="Salesforce Kennedy ERP",
        )
    )
    print(f"✅ Created goal: {goal2.title} (ID: {goal2.id})")
    
    # Goal 3: Customer Retention
    goal3 = goals_service.create_goal(
        tenant_id,
        CreateGoalRequest(
            title="Customer Retention",
            description="Build loyalty program to increase repeat customer rate from 28% to 35% for lawn and garden enthusiasts",
            current=142,
            target=200,
            unit="Repeat Customers",
            category=GoalCategory.CUSTOMER,
            deadline="2025-11-24",
            auto_tracked=True,
            connector_source="GrandNode",
        )
    )
    print(f"✅ Created goal: {goal3.title} (ID: {goal3.id})")
    
    # Display summary
    all_goals = goals_service.get_goals(tenant_id)
    print(f"\n📊 Total goals for {tenant_id}: {len(all_goals)}")
    print("\nGoals:")
    for goal in all_goals:
        progress = (goal.current / goal.target * 100) if goal.target > 0 else 0
        print(f"  • {goal.title}: {goal.current}/{goal.target} {goal.unit} ({progress:.1f}%)")


if __name__ == "__main__":
    print("🌱 Seeding CycloneRake.com demo goals...\n")
    asyncio.run(seed_cyclonerake_goals())
    print("\n✨ Done! Goals are ready for the demo.")
