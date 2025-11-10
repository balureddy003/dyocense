#!/usr/bin/env python3
"""
Test script for Conversational AI Coach with streaming

Usage:
    python test_conversational_coach.py
"""
import asyncio
import json
import os
import sys

# Add packages to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from services.smb_gateway.conversational_coach import (
    ConversationalCoachAgent,
    ChatMessage,
)


async def test_streaming():
    """Test streaming response generation"""
    print("=" * 60)
    print("Testing Conversational AI Coach with Streaming")
    print("=" * 60)
    
    # Create coach instance
    coach = ConversationalCoachAgent()
    
    # Test business context
    business_context = {
        "business_name": "TestCo Retail",
        "industry": "retail",
        "health_score": {
            "score": 75,
            "trend": "up",
            "breakdown": {
                "revenue": 80,
                "operations": 70,
                "customer": 75,
            }
        },
        "goals": [
            {
                "id": "1",
                "title": "Increase monthly revenue",
                "target_value": 50000,
                "current_value": 35000,
                "status": "ACTIVE"
            },
            {
                "id": "2",
                "title": "Improve customer satisfaction",
                "target_value": 90,
                "current_value": 78,
                "status": "ACTIVE"
            }
        ],
        "tasks": [
            {
                "id": "1",
                "title": "Review pricing strategy",
                "priority": "HIGH",
                "status": "TODO"
            },
            {
                "id": "2",
                "title": "Optimize inventory levels",
                "priority": "MEDIUM",
                "status": "TODO"
            }
        ]
    }
    
    # Test messages
    test_messages = [
        "Hello!",
        "How is my business doing?",
        "What should I focus on this week?",
        "Tell me about my revenue goal",
    ]
    
    for user_message in test_messages:
        print(f"\n{'=' * 60}")
        print(f"User: {user_message}")
        print(f"{'=' * 60}")
        print("AI Coach: ", end="", flush=True)
        
        # Stream response
        full_response = ""
        metadata = {}
        
        try:
            async for chunk in coach.stream_response(
                tenant_id="test-tenant",
                user_message=user_message,
                business_context=business_context,
                conversation_history=[]
            ):
                if not chunk.done:
                    print(chunk.delta, end="", flush=True)
                    full_response += chunk.delta
                metadata = chunk.metadata
            
            print()  # Newline after streaming
            
            # Print metadata
            if metadata:
                print(f"\nMetadata:")
                print(f"  Intent: {metadata.get('intent', 'unknown')}")
                print(f"  Stage: {metadata.get('conversation_stage', 'unknown')}")
            
        except Exception as e:
            print(f"\nError: {e}")
            import traceback
            traceback.print_exc()
        
        # Wait a bit between messages
        await asyncio.sleep(1)
    
    print(f"\n{'=' * 60}")
    print("Test complete!")
    print(f"{'=' * 60}")


async def test_intent_detection():
    """Test intent classification"""
    print("\n" + "=" * 60)
    print("Testing Intent Detection")
    print("=" * 60)
    
    coach = ConversationalCoachAgent()
    
    test_cases = [
        ("Hi there!", "greeting"),
        ("What are my goals?", "goal_discussion"),
        ("Show me my tasks", "task_management"),
        ("How can I improve revenue?", "seeking_advice"),
        ("What's my health score?", "performance_analysis"),
        ("Tell me a joke", "general_inquiry"),
    ]
    
    for message, expected_intent in test_cases:
        # Create minimal state
        state = {
            "messages": [{"role": "user", "content": message}],
            "business_context": {},
            "current_intent": None,
            "conversation_stage": "understanding",
            "user_profile": {},
            "action_plan": []
        }
        
        # Analyze intent
        result = coach._analyze_intent(state)
        detected_intent = result.get("current_intent", "unknown")
        
        status = "✓" if detected_intent == expected_intent else "✗"
        print(f"{status} '{message}'")
        print(f"  Expected: {expected_intent}, Detected: {detected_intent}")


async def test_action_planning():
    """Test action plan generation"""
    print("\n" + "=" * 60)
    print("Testing Action Plan Generation")
    print("=" * 60)
    
    coach = ConversationalCoachAgent()
    
    # Create state with business context
    state = {
        "messages": [
            {"role": "user", "content": "How can I improve my business?"}
        ],
        "business_context": {
            "business_name": "TestCo",
            "health_score": {
                "score": 60,
                "breakdown": {
                    "revenue": 50,
                    "operations": 65,
                    "customer": 70
                }
            },
            "goals": [
                {"title": "Increase revenue", "current_value": 30000, "target_value": 50000}
            ],
            "tasks": [
                {"title": "Review pricing", "priority": "HIGH"}
            ]
        },
        "current_intent": "seeking_advice",
        "conversation_stage": "advising",
        "user_profile": {},
        "action_plan": []
    }
    
    # Generate action plan
    result = coach._suggest_actions(state)
    action_plan = result.get("action_plan", [])
    
    print(f"Generated {len(action_plan)} action items:")
    for i, action in enumerate(action_plan, 1):
        print(f"  {i}. {action}")


async def main():
    """Run all tests"""
    print("\n🚀 Starting Conversational Coach Tests\n")
    
    # Check LangGraph availability
    from services.smb_gateway.conversational_coach import LANGGRAPH_AVAILABLE
    if LANGGRAPH_AVAILABLE:
        print("✓ LangGraph is available")
    else:
        print("⚠️  LangGraph not available - using fallback mode")
    
    # Check LLM configuration
    llm_provider = os.getenv("LLM_PROVIDER", "not set")
    print(f"✓ LLM Provider: {llm_provider}")
    
    # Run tests
    try:
        await test_intent_detection()
        await test_action_planning()
        await test_streaming()
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
    except Exception as e:
        print(f"\n\nTest failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
