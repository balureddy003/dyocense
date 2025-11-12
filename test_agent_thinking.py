#!/usr/bin/env python3
"""
Quick test to verify agent thinking is generated properly
"""
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.smb_gateway.task_planner import TaskPlannerAgent

def test_agent_thinking():
    """Test that agents generate thinking and evidence"""
    
    # Sample inventory data
    inventory = [
        {"StockCode": "A001", "Description": "Widget", "Quantity": 100, "UnitPrice": 10.50},
        {"StockCode": "A002", "Description": "Gadget", "Quantity": 50, "UnitPrice": 25.00},
        {"StockCode": "A003", "Description": "Doohickey", "Quantity": 0, "UnitPrice": 15.00},
        {"StockCode": "A004", "Description": "Thingamajig", "Quantity": 200, "UnitPrice": 5.00},
        {"StockCode": "A005", "Description": "Whatchamacallit", "Quantity": 5, "UnitPrice": 50.00},
    ]
    
    data = {"inventory": inventory}
    
    # Create task planner
    planner = TaskPlannerAgent()
    
    print("=" * 80)
    print("Testing Agent Thinking and Evidence Generation")
    print("=" * 80)
    
    # Test 1: Schema Discovery
    print("\n🔍 Test 1: Schema Discovery")
    print("-" * 40)
    schema_result = planner._discover_schema(data)
    
    if "agent_thoughts" in schema_result:
        print(f"✅ Agent thoughts generated: {len(schema_result['agent_thoughts'])} thoughts")
        for thought in schema_result["agent_thoughts"]:
            print(f"\n  Agent: {thought['agent']}")
            print(f"  💭 Thought: {thought['thought']}")
            print(f"  ⚡ Action: {thought['action']}")
            print(f"  👁️  Observation: {thought['observation']}")
    else:
        print("❌ No agent thoughts found!")
        return False
    
    if "evidence" in schema_result:
        print(f"\n✅ Evidence generated: {len(schema_result['evidence'])} pieces")
        for ev in schema_result["evidence"]:
            print(f"\n  📊 {ev['claim']}")
            print(f"     Calculation: {ev['calculation']}")
            print(f"     Confidence: {ev['confidence']*100:.0f}%")
    else:
        print("❌ No evidence found!")
        return False
    
    # Test 2: Volume Analysis
    print("\n\n📦 Test 2: Volume Analysis")
    print("-" * 40)
    volume_result = planner._analyze_inventory_volume(inventory)
    
    if "agent_thoughts" in volume_result:
        print(f"✅ Agent thoughts: {len(volume_result['agent_thoughts'])} thoughts")
        for thought in volume_result["agent_thoughts"]:
            print(f"\n  💭 {thought['thought']}")
            print(f"  ⚡ {thought['action']}")
            print(f"  👁️  {thought['observation']}")
    else:
        print("❌ No agent thoughts!")
        return False
    
    if "evidence" in volume_result:
        print(f"\n✅ Evidence: {len(volume_result['evidence'])} pieces")
        for ev in volume_result["evidence"]:
            print(f"  📊 {ev['claim']}")
    else:
        print("❌ No evidence!")
        return False
    
    # Test 3: Value Analysis
    print("\n\n💰 Test 3: Value Analysis")
    print("-" * 40)
    value_result = planner._analyze_inventory_value(inventory)
    
    if "agent_thoughts" in value_result and "evidence" in value_result:
        print(f"✅ Agent thoughts: {len(value_result['agent_thoughts'])}")
        print(f"✅ Evidence: {len(value_result['evidence'])}")
        print(f"\n  Total Value: ${value_result['total_value']:,.2f}")
        for ev in value_result["evidence"]:
            print(f"  📊 {ev['claim']}")
    else:
        print("❌ Missing thinking or evidence!")
        return False
    
    # Test 4: Top Products
    print("\n\n⭐ Test 4: Top Products")
    print("-" * 40)
    top_result = planner._identify_top_products(inventory)
    
    if "agent_thoughts" in top_result and "evidence" in top_result:
        print(f"✅ Agent thoughts: {len(top_result['agent_thoughts'])}")
        print(f"✅ Evidence: {len(top_result['evidence'])}")
        print(f"\n  Top Products:")
        for prod in top_result["top_10_products"][:3]:
            print(f"    - {prod['description']}: {prod['quantity']} units")
    else:
        print("❌ Missing thinking or evidence!")
        return False
    
    # Test 5: Stock Issues
    print("\n\n⚠️  Test 5: Stock Issues")
    print("-" * 40)
    stock_result = planner._detect_stock_issues(inventory)
    
    if "agent_thoughts" in stock_result and "evidence" in stock_result:
        print(f"✅ Agent thoughts: {len(stock_result['agent_thoughts'])}")
        print(f"✅ Evidence: {len(stock_result['evidence'])}")
        print(f"\n  Low stock: {stock_result['low_stock_count']}")
        print(f"  Out of stock: {stock_result['out_of_stock_count']}")
        print(f"  Total needing attention: {stock_result['items_needing_attention']}")
    else:
        print("❌ Missing thinking or evidence!")
        return False
    
    print("\n" + "=" * 80)
    print("✅ ALL TESTS PASSED!")
    print("=" * 80)
    print("\n📊 Summary:")
    print(f"  - All analysis methods generate agent thoughts")
    print(f"  - All analysis methods generate evidence")
    print(f"  - Reports will be easy to understand for SMB users")
    print(f"  - Thinking process is transparent and auditable")
    print("\n🎉 Agents are now ready to generate comprehensive reports!")
    
    return True

if __name__ == "__main__":
    try:
        success = test_agent_thinking()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
