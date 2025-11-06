#!/usr/bin/env python3
"""
End-to-End Restaurant Test Case
Simulates a complete restaurant optimization flow with realistic data.
"""
import json
import time
import requests
from typing import Dict, Any

# Configuration
API_BASE = "http://localhost:8001"
TENANT_ID = "test-restaurant-001"
PROJECT_ID = "optimize-food-costs"

# Mock auth token (in production, this would come from Keycloak)
AUTH_TOKEN = f"Bearer {TENANT_ID}"

def api_request(method: str, endpoint: str, data: Dict[Any, Any] = None) -> Dict[Any, Any]:
    """Make API request with auth headers."""
    url = f"{API_BASE}{endpoint}"
    headers = {
        "Authorization": AUTH_TOKEN,
        "Content-Type": "application/json",
    }
    
    if method == "GET":
        response = requests.get(url, headers=headers)
    elif method == "POST":
        response = requests.post(url, json=data, headers=headers)
    else:
        raise ValueError(f"Unsupported method: {method}")
    
    if response.status_code >= 400:
        print(f"❌ Error: {response.status_code}")
        print(response.text)
        response.raise_for_status()
    
    return response.json()


def print_section(title: str):
    """Print formatted section header."""
    print(f"\n{'=' * 80}")
    print(f"  {title}")
    print(f"{'=' * 80}\n")


def main():
    print_section("🍽️  RESTAURANT END-TO-END TEST")
    
    # ========================================================================
    # STEP 1: Register Restaurant Tenant
    # ========================================================================
    print_section("STEP 1: Register Restaurant Tenant")
    
    tenant_data = {
        "name": "Bella Italia Restaurant",
        "owner_email": "owner@bellaitalia.com",
        "plan_tier": "professional",
        "metadata": {
            "industry": "Restaurant",
            "location": "San Francisco, CA",
            "seats": 80,
            "cuisine": "Italian"
        }
    }
    
    print("📝 Registering tenant...")
    print(json.dumps(tenant_data, indent=2))
    
    try:
        tenant_response = api_request("POST", "/v1/tenants/register", tenant_data)
        print("\n✅ Tenant registered successfully!")
        print(json.dumps(tenant_response, indent=2))
    except Exception as e:
        print(f"⚠️  Tenant may already exist, continuing... ({e})")
    
    # ========================================================================
    # STEP 2: Get Industry Recommendations
    # ========================================================================
    print_section("STEP 2: Get Restaurant Goal Recommendations")
    
    try:
        recommendations = api_request("GET", "/v1/goals/recommendations")
        print(f"✅ Got {len(recommendations.get('recommendations', []))} recommendations")
        print(f"Industry: {recommendations.get('industry')}")
        print("\nTop 3 recommendations:")
        for i, rec in enumerate(recommendations.get('recommendations', [])[:3], 1):
            print(f"\n{i}. {rec['title']}")
            print(f"   Template: {rec['template_id']}")
            print(f"   Description: {rec['description']}")
    except Exception as e:
        print(f"⚠️  Could not get recommendations: {e}")
    
    # ========================================================================
    # STEP 3: Prepare Restaurant Data
    # ========================================================================
    print_section("STEP 3: Prepare Restaurant Data")
    
    # Realistic restaurant data
    restaurant_data = {
        # Menu items with costs and prices
        "menu_items": [
            {"item": "Margherita Pizza", "cost": 4.50, "price": 14.99, "daily_demand": 25},
            {"item": "Spaghetti Carbonara", "cost": 5.20, "price": 16.99, "daily_demand": 20},
            {"item": "Chicken Parmigiana", "cost": 6.80, "price": 19.99, "daily_demand": 15},
            {"item": "Caesar Salad", "cost": 3.20, "price": 9.99, "daily_demand": 18},
            {"item": "Tiramisu", "cost": 2.50, "price": 7.99, "daily_demand": 12},
            {"item": "Lasagna", "cost": 5.50, "price": 17.99, "daily_demand": 14},
        ],
        # Ingredient inventory
        "ingredients": [
            {"name": "Flour", "unit_cost": 0.50, "current_stock": 100, "min_stock": 20, "max_stock": 200},
            {"name": "Tomatoes", "unit_cost": 1.20, "current_stock": 50, "min_stock": 15, "max_stock": 100},
            {"name": "Mozzarella", "unit_cost": 3.50, "current_stock": 30, "min_stock": 10, "max_stock": 60},
            {"name": "Chicken", "unit_cost": 4.00, "current_stock": 40, "min_stock": 15, "max_stock": 80},
            {"name": "Pasta", "unit_cost": 1.80, "current_stock": 60, "min_stock": 20, "max_stock": 120},
            {"name": "Lettuce", "unit_cost": 0.80, "current_stock": 25, "min_stock": 10, "max_stock": 50},
        ],
        # Staff scheduling
        "staff": [
            {"role": "Chef", "hourly_rate": 28, "hours_per_week": 40, "count": 2},
            {"role": "Sous Chef", "hourly_rate": 22, "hours_per_week": 40, "count": 1},
            {"role": "Line Cook", "hourly_rate": 16, "hours_per_week": 32, "count": 3},
            {"role": "Server", "hourly_rate": 12, "hours_per_week": 25, "count": 6},
            {"role": "Dishwasher", "hourly_rate": 14, "hours_per_week": 30, "count": 2},
        ],
        # Operating costs
        "fixed_costs": {
            "rent": 8500,
            "utilities": 1200,
            "insurance": 800,
            "licenses": 500,
        }
    }
    
    print("📊 Restaurant Data Summary:")
    print(f"   - Menu Items: {len(restaurant_data['menu_items'])}")
    print(f"   - Ingredients: {len(restaurant_data['ingredients'])}")
    print(f"   - Staff Roles: {len(restaurant_data['staff'])}")
    print(f"   - Monthly Fixed Costs: ${sum(restaurant_data['fixed_costs'].values()):,.2f}")
    
    # Calculate key metrics
    total_daily_demand = sum(item['daily_demand'] for item in restaurant_data['menu_items'])
    avg_ticket = sum(item['price'] * item['daily_demand'] for item in restaurant_data['menu_items']) / total_daily_demand
    avg_cost = sum(item['cost'] * item['daily_demand'] for item in restaurant_data['menu_items']) / total_daily_demand
    
    print(f"\n📈 Key Metrics:")
    print(f"   - Daily Covers: {total_daily_demand}")
    print(f"   - Average Ticket: ${avg_ticket:.2f}")
    print(f"   - Average Food Cost: ${avg_cost:.2f}")
    print(f"   - Food Cost %: {(avg_cost/avg_ticket*100):.1f}%")
    
    # ========================================================================
    # STEP 4: Create Optimization Run
    # ========================================================================
    print_section("STEP 4: Create Optimization Run")
    
    goal = """Reduce food cost percentage from 37% to 28% while maintaining quality and customer satisfaction. 
Optimize inventory levels to minimize waste and identify the most profitable menu items to promote."""
    
    run_request = {
        "goal": goal,
        "project_id": PROJECT_ID,
        "template_id": "inventory_planning",  # or "staffing_optimization"
        "horizon": 4,  # 4-week planning horizon
        "data_inputs": restaurant_data,
    }
    
    print(f"🎯 Goal: {goal}\n")
    print("📤 Submitting optimization run...")
    
    run_response = api_request("POST", "/v1/runs", run_request)
    run_id = run_response["run_id"]
    
    print(f"✅ Run created: {run_id}")
    print(f"   Status: {run_response['status']}")
    
    # ========================================================================
    # STEP 5: Poll for Completion
    # ========================================================================
    print_section("STEP 5: Wait for Optimization to Complete")
    
    max_attempts = 60
    attempt = 0
    
    print("⏳ Polling run status...")
    
    while attempt < max_attempts:
        time.sleep(2)
        attempt += 1
        
        status_response = api_request("GET", f"/v1/runs/{run_id}")
        status = status_response["status"]
        
        if attempt % 5 == 0:  # Print every 10 seconds
            print(f"   [{attempt * 2}s] Status: {status}")
        
        if status == "completed":
            print(f"\n✅ Run completed in {attempt * 2} seconds!")
            break
        elif status == "failed":
            print(f"\n❌ Run failed!")
            print(json.dumps(status_response.get("error"), indent=2))
            return
        elif status in ["pending", "running"]:
            continue
        else:
            print(f"\n⚠️  Unknown status: {status}")
            break
    
    if attempt >= max_attempts:
        print(f"\n⏰ Timeout after {max_attempts * 2} seconds")
        return
    
    # ========================================================================
    # STEP 6: Analyze Results
    # ========================================================================
    print_section("STEP 6: Analyze Optimization Results")
    
    result = status_response.get("result", {})
    
    # Solution
    solution = result.get("solution", {})
    if solution:
        print("📊 SOLUTION SUMMARY")
        print(f"   Status: {solution.get('status')}")
        print(f"   Objective Value: {solution.get('objective_value', 'N/A')}")
        
        kpis = solution.get("kpis", {})
        if kpis:
            print(f"\n   Key Performance Indicators ({len(kpis)}):")
            # Handle both dict and list formats
            if isinstance(kpis, dict):
                for name, value in list(kpis.items())[:5]:
                    print(f"      • {name}: {value}")
            elif isinstance(kpis, list):
                for kpi in kpis[:5]:
                    print(f"      • {kpi.get('name')}: {kpi.get('value')} {kpi.get('unit', '')}")
        
        decisions = solution.get("decisions", {})
        if decisions:
            print(f"\n   Decision Variables: {len(decisions)} variables set")
    
    # Explanation
    explanation = result.get("explanation", {})
    if explanation:
        print(f"\n📝 EXPLANATION")
        print(f"   {explanation.get('summary', 'No summary available')}")
        
        what_ifs = explanation.get("what_ifs", [])
        if what_ifs:
            print(f"\n   What-If Scenarios ({len(what_ifs)}):")
            for idx, scenario in enumerate(what_ifs[:3], 1):
                if isinstance(scenario, dict):
                    print(f"\n      {scenario.get('scenario')}:")
                    print(f"      → {scenario.get('impact')}")
                else:
                    print(f"\n      Scenario {idx}: {scenario}")
    
    # Diagnostics
    diagnostics = result.get("diagnostics", {})
    if diagnostics:
        print(f"\n🔍 DIAGNOSTICS")
        print(f"   Feasibility: {diagnostics.get('feasibility')}")
        print(f"   Gap: {diagnostics.get('gap', 'N/A')}")
        print(f"   Runtime: {diagnostics.get('runtime_ms', 'N/A')} ms")
    
    # Forecast
    forecasts = result.get("forecasts", [])
    if forecasts:
        print(f"\n📈 FORECASTS")
        for forecast in forecasts[:3]:
            print(f"   {forecast.get('name')}: {forecast.get('predictions', [])}")
    
    # ========================================================================
    # STEP 7: Get Evidence
    # ========================================================================
    print_section("STEP 7: Retrieve Evidence Records")
    
    try:
        evidence_response = api_request("GET", f"/v1/evidence/{run_id}")
        print(f"✅ Evidence retrieved")
        print(f"   Run ID: {evidence_response.get('run_id')}")
        print(f"   Goal: {evidence_response.get('goal')}")
        print(f"   Created: {evidence_response.get('created_at')}")
        print(f"   Artifacts: {len(evidence_response.get('artifacts', []))} files")
    except Exception as e:
        print(f"⚠️  Could not retrieve evidence: {e}")
    
    # ========================================================================
    # STEP 8: Chat Interaction
    # ========================================================================
    print_section("STEP 8: Chat with AI Assistant")
    
    chat_request = {
        "messages": [
            {
                "role": "user",
                "content": f"Based on the optimization results for run {run_id}, what are the top 3 actions I should take immediately to reduce food costs?"
            }
        ],
        "context": {
            "tenant_id": TENANT_ID,
            "run_id": run_id,
            "has_results": True,
        }
    }
    
    try:
        chat_response = api_request("POST", "/v1/chat", chat_request)
        print(f"🤖 AI Response:")
        print(f"\n{chat_response.get('reply')}\n")
    except Exception as e:
        print(f"⚠️  Chat not available: {e}")
    
    # ========================================================================
    # FINAL SUMMARY
    # ========================================================================
    print_section("✅ END-TO-END TEST COMPLETE")
    
    print("Summary:")
    print(f"   • Tenant: Bella Italia Restaurant")
    print(f"   • Goal: Reduce food cost % from 37% to 28%")
    print(f"   • Run ID: {run_id}")
    print(f"   • Status: {status}")
    print(f"   • Data Points: {len(restaurant_data['menu_items'])} menu items, {len(restaurant_data['ingredients'])} ingredients")
    print(f"   • Planning Horizon: 4 weeks")
    
    if solution:
        print(f"\n   📊 Optimization successful!")
        print(f"      - Objective: {solution.get('objective_value', 'N/A')}")
        print(f"      - Decisions: {len(solution.get('decisions', {}))} variables")
        print(f"      - KPIs: {len(solution.get('kpis', []))} metrics")
    
    print(f"\n{'=' * 80}\n")
    print("🎉 Test completed successfully!")
    print("\nNext steps:")
    print("   1. Review the optimization results above")
    print("   2. Check evidence records in artifacts/runs/")
    print("   3. Test the UI by navigating to http://localhost:5173")
    print("   4. View the run in the dashboard")
    print(f"\n{'=' * 80}\n")


if __name__ == "__main__":
    main()
