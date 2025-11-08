"""
Test script for multi-agent business goal analysis system.

Usage:
    python scripts/test_multi_agent.py "Increase sales by 20% in Q2"
"""

import asyncio
import json
import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from packages.agents.multi_agent_system import OrchestratorAgent


async def test_goal_analysis(goal: str, context: dict = None):
    """Test multi-agent goal analysis."""
    print(f"\n{'='*80}")
    print(f"Testing Multi-Agent System")
    print(f"{'='*80}")
    print(f"\nGoal: {goal}\n")
    
    # Create orchestrator
    orchestrator = OrchestratorAgent()
    
    # Configure LLM (using environment variables or defaults)
    provider = os.getenv("LLM_PROVIDER", "azure")
    
    print(f"Configuring LLM provider: {provider}")
    
    if provider == "azure":
        orchestrator.configure_llm(
            provider="azure",
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT", "https://your-endpoint.openai.azure.com/"),
            api_key=os.getenv("AZURE_OPENAI_API_KEY", "your-key-here"),
            deployment_name=os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o-mini"),
            api_version="2024-02-15-preview",
            temperature=0.2
        )
    else:
        orchestrator.configure_llm(
            provider="openai",
            api_key=os.getenv("OPENAI_API_KEY", "your-key-here"),
            model="gpt-4o-mini",
            temperature=0.2
        )
    
    # Build agent graph
    print("Building agent workflow graph...")
    orchestrator.build_graph()
    
    # Process goal
    print("\nProcessing goal through multi-agent system...\n")
    print("-" * 80)
    
    result = await orchestrator.process_goal(goal, context or {})
    
    # Display results
    print("\n" + "=" * 80)
    print("ANALYSIS COMPLETE")
    print("=" * 80)
    
    print("\n### GOAL ANALYSIS ###")
    if result.get("goal_analysis"):
        print(json.dumps(result["goal_analysis"], indent=2))
    
    print("\n### DATA ANALYSIS ###")
    if result.get("data_analysis"):
        print(json.dumps(result["data_analysis"], indent=2))
    
    print("\n### MODEL RESULTS ###")
    if result.get("model_results"):
        print(json.dumps(result["model_results"], indent=2))
    
    print("\n### RECOMMENDATIONS ###")
    if result.get("recommendations"):
        print(json.dumps(result["recommendations"], indent=2))
    
    print("\n### FINAL RESPONSE ###")
    print(result.get("response", "No response generated"))
    
    print("\n### CONVERSATION HISTORY ###")
    for i, msg in enumerate(result.get("conversation", []), 1):
        print(f"\n{i}. {msg[:200]}{'...' if len(msg) > 200 else ''}")
    
    return result


async def test_scenarios():
    """Test multiple business scenarios."""
    
    scenarios = [
        {
            "goal": "Increase sales revenue by 20% in Q2 2024",
            "context": {
                "data_analysis": {
                    "available_sources": ["CRM data", "Historical sales"],
                    "data_quality": "Good"
                }
            }
        },
        {
            "goal": "Reduce operational costs by 15%",
            "context": {}
        },
        {
            "goal": "Improve customer retention rate from 75% to 85%",
            "context": {
                "data_analysis": {
                    "available_sources": ["Customer feedback", "Support tickets"],
                    "data_quality": "Moderate"
                }
            }
        },
        {
            "goal": "Launch new product line in European market",
            "context": {}
        }
    ]
    
    for i, scenario in enumerate(scenarios, 1):
        print(f"\n\n{'#'*80}")
        print(f"# SCENARIO {i}/{len(scenarios)}")
        print(f"{'#'*80}\n")
        
        await test_goal_analysis(scenario["goal"], scenario.get("context"))
        
        if i < len(scenarios):
            print("\n\nPress Enter to continue to next scenario...")
            input()


async def main():
    """Main entry point."""
    
    # Check if goal provided as argument
    if len(sys.argv) > 1:
        goal = " ".join(sys.argv[1:])
        await test_goal_analysis(goal)
    else:
        # Run predefined scenarios
        print("No goal specified, running test scenarios...")
        print("\nAvailable test scenarios:")
        print("1. Increase sales revenue by 20%")
        print("2. Reduce operational costs by 15%")
        print("3. Improve customer retention")
        print("4. Launch new product line")
        
        choice = input("\nSelect scenario (1-4) or press Enter for all: ")
        
        if choice.strip() in ['1', '2', '3', '4']:
            scenarios = [
                "Increase sales revenue by 20% in Q2 2024",
                "Reduce operational costs by 15%",
                "Improve customer retention rate from 75% to 85%",
                "Launch new product line in European market"
            ]
            await test_goal_analysis(scenarios[int(choice) - 1])
        else:
            await test_scenarios()


if __name__ == "__main__":
    # Check dependencies
    try:
        from langgraph.graph import StateGraph
        print("✓ LangGraph available")
    except ImportError:
        print("✗ LangGraph not available")
        print("\nInstall dependencies:")
        print("  pip install langgraph langchain-openai langchain-core")
        sys.exit(1)
    
    # Run tests
    asyncio.run(main())
