#!/usr/bin/env python3
"""
Test script for multi-agent coach data connection awareness.
Tests that the coach properly detects and communicates data connection status.
"""

import asyncio
import json
from typing import Dict, Any


async def test_data_connection_awareness():
    """Test data connection awareness in multi-agent coach"""
    
    print("🧪 Testing Multi-Agent Coach Data Connection Awareness\n")
    print("=" * 70)
    
    # Test cases for different agent types and data connection states
    test_cases = [
        {
            "name": "Data Analyst - No Data",
            "message": "Analyze my sales trends",
            "has_data": False,
            "data_sources": {"orders": 0, "inventory": 0, "customers": 0},
            "expected_keywords": ["connect", "data sources", "sample data"]
        },
        {
            "name": "Data Analyst - With Data",
            "message": "Show me sales patterns",
            "has_data": True,
            "data_sources": {"orders": 150, "inventory": 45, "customers": 89},
            "expected_keywords": ["CONNECTED", "health", "analysis"]
        },
        {
            "name": "Data Scientist - No Data",
            "message": "Forecast next quarter revenue",
            "has_data": False,
            "data_sources": {"orders": 0, "inventory": 0, "customers": 0},
            "expected_keywords": ["connect", "accurate", "real data"]
        },
        {
            "name": "Goal Analyzer - No Data",
            "message": "Help me set quarterly sales goals",
            "has_data": False,
            "data_sources": {"orders": 0, "inventory": 0, "customers": 0},
            "expected_keywords": ["connect", "tracking", "data"]
        },
        {
            "name": "Business Consultant - With Data",
            "message": "What should I focus on?",
            "has_data": True,
            "data_sources": {"orders": 200, "inventory": 60, "customers": 120},
            "expected_keywords": ["CONNECTED", "recommendations", "business"]
        },
        {
            "name": "General Question - No Data",
            "message": "Hello, how can you help?",
            "has_data": False,
            "data_sources": {"orders": 0, "inventory": 0, "customers": 0},
            "expected_keywords": ["connect", "data sources", "insights"]
        }
    ]
    
    # Import the multi-agent coach
    try:
        import sys
        sys.path.insert(0, '/Users/balu/Projects/dyocense/services/smb_gateway')
        from multi_agent_coach import MultiAgentCoach
        
        coach = MultiAgentCoach()
        print("✅ Multi-agent coach initialized\n")
    except Exception as e:
        print(f"❌ Failed to initialize coach: {e}")
        return
    
    # Run test cases
    passed = 0
    failed = 0
    
    for i, test in enumerate(test_cases, 1):
        print(f"\n{i}. Testing: {test['name']}")
        print("-" * 70)
        print(f"Message: '{test['message']}'")
        print(f"Has Data: {test['has_data']}")
        print(f"Data Sources: {test['data_sources']}")
        
        # Build business context
        business_context = {
            "business_name": "Test Business",
            "has_data_connected": test['has_data'],
            "data_sources": test['data_sources']
        }
        
        if test['has_data']:
            business_context["health_score"] = {
                "score": 75,
                "breakdown": {
                    "revenue": 80,
                    "operations": 70,
                    "customer": 75
                }
            }
        
        # Detect intent
        agent_type = coach._detect_specialized_intent(test['message'])
        print(f"Detected Agent: {agent_type or 'general'}")
        
        # Build prompt (simulated - we'll check the prompt content)
        if agent_type:
            # Simulate agent results
            agent_results = {
                "intent": agent_type,
                "message": test['message'],
                "simulated": True
            }
            
            prompt = coach._build_specialized_prompt(
                agent_type=agent_type,
                user_message=test['message'],
                agent_results=agent_results,
                business_context=business_context
            )
        else:
            prompt = coach._build_general_prompt(
                user_message=test['message'],
                context=business_context
            )
        
        print(f"\nGenerated Prompt Length: {len(prompt)} chars")
        
        # Check for expected keywords
        found_keywords = []
        missing_keywords = []
        
        for keyword in test['expected_keywords']:
            if keyword.lower() in prompt.lower():
                found_keywords.append(keyword)
            else:
                missing_keywords.append(keyword)
        
        # Display results
        if found_keywords:
            print(f"✅ Found keywords: {', '.join(found_keywords)}")
        
        if missing_keywords:
            print(f"⚠️  Missing keywords: {', '.join(missing_keywords)}")
        
        # Show relevant prompt sections
        if test['has_data']:
            if "✅ BUSINESS DATA CONNECTED" in prompt:
                print("✅ Prompt includes data connection confirmation")
                passed += 1
            else:
                print("❌ Prompt missing data connection confirmation")
                failed += 1
        else:
            if "⚠️ NO REAL DATA CONNECTED" in prompt or "NO DATA CONNECTED" in prompt:
                print("✅ Prompt includes data connection warning")
                passed += 1
            else:
                print("❌ Prompt missing data connection warning")
                failed += 1
                # Show prompt for debugging
                print("\nPrompt Preview (first 500 chars):")
                print(prompt[:500])
    
    # Summary
    print("\n" + "=" * 70)
    print(f"\n📊 Test Summary:")
    print(f"✅ Passed: {passed}/{len(test_cases)}")
    print(f"❌ Failed: {failed}/{len(test_cases)}")
    print(f"Success Rate: {(passed/len(test_cases)*100):.1f}%")
    
    if failed == 0:
        print("\n🎉 All tests passed! Data connection awareness is working correctly.")
    else:
        print(f"\n⚠️  {failed} test(s) failed. Review prompt generation logic.")
    
    print("=" * 70)


async def test_streaming_response():
    """Test that streaming responses include data connection messaging"""
    
    print("\n\n🌊 Testing Streaming Response with Data Awareness\n")
    print("=" * 70)
    
    try:
        import sys
        sys.path.insert(0, '/Users/balu/Projects/dyocense/services/smb_gateway')
        from multi_agent_coach import MultiAgentCoach
        
        coach = MultiAgentCoach()
        
        # Test streaming with no data
        print("\nTest: Streaming with NO data connected")
        print("-" * 70)
        
        business_context = {
            "business_name": "Demo Shop",
            "has_data_connected": False,
            "data_sources": {"orders": 0, "inventory": 0, "customers": 0}
        }
        
        collected_response = ""
        chunk_count = 0
        
        async for chunk in coach.stream_response(
            tenant_id="test-tenant",
            user_message="What are my top selling products?",
            business_context=business_context
        ):
            if chunk.delta:
                collected_response += chunk.delta
                chunk_count += 1
        
        print(f"\nReceived {chunk_count} chunks")
        print(f"Total response length: {len(collected_response)} chars")
        print("\nResponse Preview:")
        print(collected_response[:500])
        
        # Check for data connection messaging
        if any(keyword in collected_response.lower() for keyword in ["connect", "data source", "sample"]):
            print("\n✅ Streaming response includes data connection messaging")
        else:
            print("\n⚠️  Streaming response may be missing data connection messaging")
            print("\nFull response:")
            print(collected_response)
        
    except Exception as e:
        print(f"❌ Streaming test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("Multi-Agent Coach Data Connection Awareness Test Suite")
    print("=" * 70)
    
    asyncio.run(test_data_connection_awareness())
    # asyncio.run(test_streaming_response())  # Commented out - requires LLM
    
    print("\n✅ Testing complete!\n")
