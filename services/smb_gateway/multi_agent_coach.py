"""
Multi-Agent Business Coach

Orchestrates specialized agents for different business tasks:
- Data Analyst: Analyzes data quality, patterns, and availability
- Data Scientist: Forecasting, optimization, statistical analysis
- Business Consultant: Strategic recommendations and action plans
- Goal Analyzer: SMART goal decomposition and validation
"""
from __future__ import annotations

import asyncio
import json
import logging
import os
import sys
from datetime import datetime
from typing import Any, AsyncGenerator, Dict, List, Optional, TypedDict

from pydantic import BaseModel, Field

# Add packages to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from packages.llm import _invoke_llm
from .coach_service import ChatMessage

logger = logging.getLogger(__name__)

# Try to import multi-agent system
try:
    from packages.agents.multi_agent_system import (
        AgentState as MultiAgentState,
        GoalAnalyzerAgent,
        DataAnalystAgent,
        DataScientistAgent,
        BusinessConsultantAgent,
        MultiAgentOrchestrator,
        LANGGRAPH_AVAILABLE
    )
    MULTI_AGENT_AVAILABLE = True
except ImportError:
    logger.warning("Multi-agent system not available, using single-agent fallback")
    MULTI_AGENT_AVAILABLE = False


class StreamChunk(BaseModel):
    """Streaming response chunk"""
    delta: str
    done: bool = False
    metadata: Dict[str, Any] = Field(default_factory=dict)


class AgentState(TypedDict):
    """Simplified state for coach conversations"""
    messages: List[Dict[str, str]]
    business_context: Dict[str, Any]
    current_intent: Optional[str]
    conversation_stage: str
    user_profile: Dict[str, Any]
    action_plan: List[str]
    active_agent: Optional[str]  # Which specialist agent is active
    agent_results: Dict[str, Any]  # Results from specialist agents


class MultiAgentCoach:
    """Business coach with specialized agent orchestration"""
    
    def __init__(self):
        self.conversations: Dict[str, AgentState] = {}
        
        if MULTI_AGENT_AVAILABLE:
            # Initialize orchestrator
            self.orchestrator = MultiAgentOrchestrator()
            logger.info("Multi-agent orchestrator initialized")
        else:
            self.orchestrator = None
            logger.warning("Multi-agent orchestrator not available")
    
    def _detect_specialized_intent(self, user_message: str, context: Dict[str, Any]) -> Optional[str]:
        """Detect if query requires a specialized agent"""
        msg_lower = user_message.lower()
        
        # Data Analysis questions
        if any(word in msg_lower for word in [
            "data", "analyze", "analysis", "trend", "pattern", "insight",
            "metric", "kpi", "dashboard", "report", "statistics"
        ]):
            return "data_analyst"
        
        # Data Science questions (forecasting, optimization, modeling)
        if any(word in msg_lower for word in [
            "forecast", "predict", "prediction", "optimize", "optimization",
            "model", "algorithm", "machine learning", "trend forecast",
            "demand forecast", "revenue forecast", "inventory optimize"
        ]):
            return "data_scientist"
        
        # Goal-related questions
        if any(word in msg_lower for word in [
            "goal", "objective", "target", "milestone", "smart goal",
            "achieve", "plan", "strategy"
        ]):
            # Check if they need goal decomposition vs simple info
            if any(word in msg_lower for word in ["set", "create", "define", "break down", "how to"]):
                return "goal_analyzer"
        
        # Task/Action Plan generation
        if any(word in msg_lower for word in [
            "task", "action plan", "weekly plan", "to-do", "what should i do",
            "prioritize", "focus on", "work on", "this week"
        ]):
            return "goal_analyzer"  # Goal analyzer handles action planning
        
        # Strategic/business consulting
        if any(word in msg_lower for word in [
            "strategy", "recommend", "advice", "should I", "what if",
            "improve", "grow", "scale", "expand", "competitive"
        ]):
            return "business_consultant"
        
        return None
    
    async def _invoke_specialized_agent(
        self,
        agent_type: str,
        user_message: str,
        business_context: Dict[str, Any],
        tenant_id: str = None
    ) -> Dict[str, Any]:
        """Invoke a specialized agent for analysis or recommendations"""
        
        if not MULTI_AGENT_AVAILABLE:
            return {"error": "Multi-agent system not available"}
        
        # Get data for this business
        data_sources = business_context.get("data_sources", {})
        health_score = business_context.get("health_score", {})
        goals = business_context.get("goals", [])
        tasks = business_context.get("tasks", [])
        metrics = business_context.get("metrics", {})
        
        # Check for available connectors for this tenant
        available_connectors = []
        if tenant_id:
            try:
                from packages.agents.mcp_tools import get_tenant_connectors
                available_connectors = get_tenant_connectors(tenant_id)
                logger.info(f"Tenant {tenant_id} has connectors: {available_connectors}")
            except Exception as e:
                logger.warning(f"Could not get tenant connectors: {e}")
        
        # Prepare state for orchestrator with actual business data
        state: MultiAgentState = {
            "messages": [],
            "user_goal": user_message,
            "current_agent": agent_type,
            "goal_analysis": None,
            "data_analysis": None,
            "model_results": None,
            "recommendations": None,
            "next_agent": None,
            "final_response": None,
            "iteration_count": 0,
            "max_iterations": 3
        }
        
        # Build comprehensive context message with actual data insights
        metrics = business_context.get("metrics", {})
        context_msg = f"""
Business Context for {business_context.get('business_name', 'the business')}:

DATA AVAILABILITY:
- Orders: {data_sources.get('orders', 0)} records
- Inventory: {data_sources.get('inventory', 0)} items
- Customers: {data_sources.get('customers', 0)} records
- Data Type: {"Sample/Demo Data" if not business_context.get('has_data_connected') else "Real Connected Data"}

KEY BUSINESS METRICS:
- Revenue (Last 30 Days): ${metrics.get('revenue_last_30_days', 0):,.2f}
- Orders (Last 30 Days): {metrics.get('orders_last_30_days', 0)}
- Average Order Value: ${metrics.get('avg_order_value', 0):,.2f}
- Total Customers: {metrics.get('total_customers', 0)}
- VIP Customers: {metrics.get('vip_customers', 0)}
- Repeat Customer Rate: {metrics.get('repeat_customer_rate', 0)}%
- Low Stock Items: {metrics.get('low_stock_items', 0)}
- Out of Stock Items: {metrics.get('out_of_stock_items', 0)}
- Total Inventory Value: ${metrics.get('total_inventory_value', 0):,.2f}

CONNECTED DATA SOURCES:
{f"- {', '.join(available_connectors)}" if available_connectors else "- None (using sample data)"}

CURRENT BUSINESS HEALTH:
- Overall Score: {health_score.get('score', 0)}/100
- Trend: {health_score.get('trend', 0)}
- Revenue Health: {health_score.get('breakdown', {}).get('revenue', 0)}/100
- Operations Health: {health_score.get('breakdown', {}).get('operations', 0)}/100
- Customer Health: {health_score.get('breakdown', {}).get('customer', 0)}/100

ACTIVE INITIATIVES:
- Active Goals: {len(goals)}
- Pending Tasks: {len(tasks)}

{"⚠️ NOTE: Using sample data. Encourage user to connect real data sources for accurate analysis." if not business_context.get('has_data_connected') else "✅ Using real connected business data."}

User Question: {user_message}
"""
        
        try:
            # Run agent-specific logic with context
            if agent_type == "data_analyst":
                # Provide analysis based on actual metrics
                analysis = {
                    "intent": "data_analysis",
                    "question": user_message,
                    "data_available": {
                        "orders": data_sources.get('orders', 0),
                        "inventory": data_sources.get('inventory', 0),
                        "customers": data_sources.get('customers', 0),
                    },
                    "health_metrics": health_score,
                    "insights": [
                        f"Business health score is {health_score.get('score', 0)}/100",
                        f"Revenue health: {health_score.get('breakdown', {}).get('revenue', 0)}/100",
                        f"Operations health: {health_score.get('breakdown', {}).get('operations', 0)}/100",
                        f"Customer health: {health_score.get('breakdown', {}).get('customer', 0)}/100",
                    ],
                    "data_quality": "sample" if not business_context.get('has_data_connected') else "real",
                    "context": context_msg
                }
                return analysis
            
            elif agent_type == "data_scientist":
                # Provide forecasting context based on available data
                forecast = {
                    "intent": "forecasting",
                    "question": user_message,
                    "available_data_points": data_sources.get('orders', 0),
                    "current_trend": health_score.get('trend', 0),
                    "confidence": "low" if not business_context.get('has_data_connected') else "high",
                    "recommendations": [
                        f"Current trend: {health_score.get('trend', 0)}%",
                        "Connect real data for accurate forecasting" if not business_context.get('has_data_connected') else "Sufficient data for forecasting"
                    ],
                    "data_quality": "sample" if not business_context.get('has_data_connected') else "real",
                    "context": context_msg
                }
                return forecast
            
            elif agent_type == "goal_analyzer":
                # Analyze goals with current progress context
                goal_analysis = {
                    "intent": "goal_planning",
                    "question": user_message,
                    "current_goals": len(goals),
                    "current_tasks": len(tasks),
                    "business_health": health_score.get('score', 0),
                    "recommendations": [
                        f"You have {len(goals)} active goals",
                        f"Current business health: {health_score.get('score', 0)}/100",
                        "Connect data for automatic goal tracking" if not business_context.get('has_data_connected') else "Data connected for goal tracking"
                    ],
                    "goals_list": [g.get('title', 'Untitled') for g in goals[:3]],
                    "context": context_msg
                }
                return goal_analysis
            
            elif agent_type == "business_consultant":
                # Strategic recommendations based on health metrics
                recommendations = {
                    "intent": "strategic_advice",
                    "question": user_message,
                    "health_assessment": {
                        "overall": health_score.get('score', 0),
                        "revenue": health_score.get('breakdown', {}).get('revenue', 0),
                        "operations": health_score.get('breakdown', {}).get('operations', 0),
                        "customer": health_score.get('breakdown', {}).get('customer', 0),
                    },
                    "focus_areas": [],
                    "data_quality": "sample" if not business_context.get('has_data_connected') else "real",
                    "context": context_msg
                }
                
                # Identify focus areas based on health scores
                breakdown = health_score.get('breakdown', {})
                if breakdown.get('revenue', 100) < 60:
                    recommendations["focus_areas"].append("Revenue improvement")
                if breakdown.get('operations', 100) < 60:
                    recommendations["focus_areas"].append("Operations efficiency")
                if breakdown.get('customer', 100) < 60:
                    recommendations["focus_areas"].append("Customer retention")
                
                return recommendations
            
            else:
                return {"error": f"Unknown agent type: {agent_type}"}
                
        except Exception as e:
            logger.error(f"Agent invocation failed: {e}")
            return {"error": str(e), "context": context_msg}
    
    def _build_specialized_prompt(
        self,
        user_message: str,
        business_context: Dict[str, Any],
        agent_type: str,
        agent_results: Dict[str, Any]
    ) -> str:
        """Build prompt incorporating specialist agent results"""
        
        business_name = business_context.get("business_name", "your business")
        has_data = business_context.get("has_data_connected", False)
        
        prompt = f"""You are a friendly AI business coach for {business_name}.

SPECIALIST AGENT: {agent_type.replace('_', ' ').title()}

The user asked: "{user_message}"

"""
        
        # Add agent-specific context
        if agent_type == "data_analyst":
            prompt += f"""
DATA ANALYSIS RESULTS:
{json.dumps(agent_results, indent=2)}

Your role: Translate these data insights into friendly, actionable advice.
- Explain patterns in simple terms
- Highlight key findings
- Suggest what to investigate further
- Recommend actions based on the data

⚠️ DATA STATUS: {"CONNECTED - Real business data" if has_data else "NOT CONNECTED - Using sample data"}
{f"IMPORTANT: Since no real data is connected, gently encourage them to connect their business data sources for accurate insights." if not has_data else ""}
"""
        
        elif agent_type == "data_scientist":
            prompt += f"""
DATA SCIENCE RESULTS:
{json.dumps(agent_results, indent=2)}

Your role: Explain these technical results in business terms.
- Translate forecasts into business impact
- Explain confidence levels simply
- Provide actionable recommendations
- Highlight risks and opportunities

⚠️ DATA STATUS: {"CONNECTED - Real business data" if has_data else "NOT CONNECTED - Using sample data"}
{f"IMPORTANT: Since no real data is connected, forecasts are based on sample data. Strongly encourage connecting real data for accurate predictions." if not has_data else ""}
"""
        
        elif agent_type == "goal_analyzer":
            prompt += f"""
GOAL ANALYSIS RESULTS:
{json.dumps(agent_results, indent=2)}

Your role: Help them refine and achieve their goal.
- Validate if the goal is SMART
- Break down into smaller milestones
- Suggest metrics to track
- Provide timeline guidance

⚠️ DATA STATUS: {"CONNECTED - Can track progress with real data" if has_data else "NOT CONNECTED - Limited tracking capability"}
{f"IMPORTANT: Mention that connecting data will enable automatic progress tracking and real-time goal monitoring." if not has_data else ""}
"""
        
        elif agent_type == "business_consultant":
            prompt += f"""
STRATEGIC RECOMMENDATIONS:
{json.dumps(agent_results, indent=2)}

Your role: Provide strategic guidance.
- Explain recommendations clearly
- Prioritize actions
- Consider their resources and constraints
- Offer alternative approaches

⚠️ DATA STATUS: {"CONNECTED - Recommendations based on real data" if has_data else "NOT CONNECTED - Recommendations are generic"}
{f"IMPORTANT: Explain that connecting data will enable personalized, data-driven recommendations specific to their business." if not has_data else ""}
"""
        
        # Add business context with specific insights
        if has_data:
            health = business_context.get("health_score", {})
            data_sources = business_context.get("data_sources", {})
            prompt += f"""

✅ BUSINESS DATA CONNECTED:
- Orders: {data_sources.get('orders', 0)} orders
- Inventory: {data_sources.get('inventory', 0)} items
- Customers: {data_sources.get('customers', 0)} customers

CURRENT BUSINESS HEALTH:
- Overall Score: {health.get('score', 'N/A')}/100 (Trend: {health.get('trend', 0):+.1f}%)
- Revenue Health: {health.get('breakdown', {}).get('revenue', 'N/A')}/100
- Operations Health: {health.get('breakdown', {}).get('operations', 'N/A')}/100
- Customer Health: {health.get('breakdown', {}).get('customer', 'N/A')}/100

IMPORTANT: Use these specific numbers in your response. For example:
- If discussing sales: "With {data_sources.get('orders', 0)} orders..."
- If discussing inventory: "Looking at your {data_sources.get('inventory', 0)} items..."
- If discussing customers: "Among your {data_sources.get('customers', 0)} customers..."
"""
        else:
            data_sources = business_context.get("data_sources", {})
            health = business_context.get("health_score", {})
            prompt += f"""

⚠️ NO REAL DATA CONNECTED (Using Sample Data):
- Sample Orders: {data_sources.get('orders', 0)} orders
- Sample Inventory: {data_sources.get('inventory', 0)} items
- Sample Customers: {data_sources.get('customers', 0)} customers

CURRENT METRICS (from sample data):
- Overall Health: {health.get('score', 'N/A')}/100
- Revenue Health: {health.get('breakdown', {}).get('revenue', 'N/A')}/100
- Operations Health: {health.get('breakdown', {}).get('operations', 'N/A')}/100

TO GET ACCURATE INSIGHTS, connect real data:
📦 E-commerce: Shopify, WooCommerce, GrandNode
👥 CRM: Salesforce, HubSpot
💰 Accounting: QuickBooks, Xero

IMPORTANT: While you can analyze the sample data ({data_sources.get('orders', 0)} orders, {data_sources.get('inventory', 0)} items), 
ALWAYS mention that connecting real data will provide:
✨ Real-time business health monitoring
📊 Accurate {agent_type.replace('_', ' ')} analysis specific to their business
🎯 Personalized recommendations based on actual patterns
📈 Reliable trend analysis and forecasting
"""
        
        prompt += """

RESPONSE GUIDELINES:
1. Be conversational and friendly (2-4 sentences)
2. Reference specific insights from the specialist agent
3. Use simple language, avoid jargon
4. Provide 2-3 concrete action items
5. Ask a follow-up question if helpful
6. Use emojis sparingly: 📊 📈 💡 🎯 ✨

Respond naturally to help them understand and act on the analysis."""
        
        return prompt
    
    async def stream_response(
        self,
        tenant_id: str,
        user_message: str,
        business_context: Dict[str, Any],
        conversation_history: List[ChatMessage]
    ) -> AsyncGenerator[StreamChunk, None]:
        """Stream conversational response, delegating to specialized agents when needed"""
        
        # Initialize conversation state
        if tenant_id not in self.conversations:
            self.conversations[tenant_id] = AgentState(
                messages=[],
                business_context=business_context,
                current_intent=None,
                conversation_stage="greeting",
                user_profile={},
                action_plan=[],
                active_agent=None,
                agent_results={}
            )
        
        state = self.conversations[tenant_id]
        state["business_context"] = business_context
        
        # Detect if we need a specialized agent
        specialized_agent = self._detect_specialized_intent(user_message, business_context)
        
        response_text = ""
        
        if specialized_agent and MULTI_AGENT_AVAILABLE:
            # Delegate to specialist
            logger.info(f"Delegating to specialist: {specialized_agent}")
            start_ts = datetime.now()
            
            # Yield thinking message
            yield StreamChunk(
                delta=f"🤔 Consulting our {specialized_agent.replace('_', ' ')}...\n\n",
                done=False,
                metadata={
                    "agent": specialized_agent,
                    "status": "thinking",
                    "tool_event": {
                        "type": "start",
                        "name": f"agent:{specialized_agent}",
                        "ts": start_ts.isoformat()
                    }
                }
            )
            
            # Invoke specialist agent
            agent_results = await self._invoke_specialized_agent(
                specialized_agent,
                user_message,
                business_context,
                tenant_id
            )
            
            state["active_agent"] = specialized_agent
            state["agent_results"] = agent_results
            
            # Build prompt with agent results
            prompt = self._build_specialized_prompt(
                user_message,
                business_context,
                specialized_agent,
                agent_results
            )
            
            # Generate response
            try:
                response_text = _invoke_llm(prompt)
                
                if response_text:
                    # Stream the response word by word
                    words = response_text.split()
                    for i, word in enumerate(words):
                        # Prepare tracing metadata on final chunk
                        is_last = (i == len(words) - 1)
                        tracing_enabled = os.getenv("LANGCHAIN_TRACING_V2", "").lower() == "true"
                        metadata: Dict[str, Any] = {
                            "agent": specialized_agent,
                            "stage": "responding",
                        }
                        if is_last:
                            end_ts = datetime.now()
                            latency_ms = max(0, int((end_ts - start_ts).total_seconds() * 1000))
                            metadata.update({
                                "tracing_enabled": tracing_enabled,
                                "project": os.getenv("LANGCHAIN_PROJECT"),
                                # run_url can be set by backend when available
                                # UI should only show Trace button when present
                                "run_url": os.getenv("LANGCHAIN_RUN_URL"),
                                "tool_event": {
                                    "type": "end",
                                    "name": f"agent:{specialized_agent}",
                                    "ts": end_ts.isoformat(),
                                    "latency_ms": latency_ms
                                }
                            })
                        yield StreamChunk(
                            delta=word + " ",
                            done=is_last,
                            metadata=metadata
                        )
                        await asyncio.sleep(0.05)
                else:
                    # Fallback
                    fallback = self._generate_fallback(specialized_agent, user_message)
                    yield StreamChunk(delta=fallback, done=True, metadata={"agent": "fallback"})
                    
            except Exception as e:
                logger.error(f"LLM error: {e}")
                error_msg = "I encountered an issue processing that. Could you rephrase?"
                yield StreamChunk(delta=error_msg, done=True, metadata={"error": str(e)})
        
        else:
            # General conversation (no specialist needed)
            prompt = self._build_general_prompt(user_message, business_context)
            
            try:
                response_text = _invoke_llm(prompt)
                
                if response_text:
                    words = response_text.split()
                    for i, word in enumerate(words):
                        is_last = (i == len(words) - 1)
                        tracing_enabled = os.getenv("LANGCHAIN_TRACING_V2", "").lower() == "true"
                        metadata: Dict[str, Any] = {"agent": "general_coach"}
                        
                        # Add rich visual data on final chunk for revenue/metrics questions
                        if is_last and any(keyword in user_message.lower() for keyword in ['revenue', 'sales', 'orders', 'customers', 'metrics']):
                            metrics = business_context.get("metrics", {})
                            metadata.update({
                                "rich_data": {
                                    "type": "metrics_card",
                                    "metrics": [
                                        {
                                            "label": "Revenue (30d)",
                                            "value": f"${metrics.get('revenue_last_30_days', 0):,.2f}",
                                            "trend": "+8%",
                                            "color": "green"
                                        },
                                        {
                                            "label": "Orders (30d)",
                                            "value": str(metrics.get('orders_last_30_days', 0)),
                                            "trend": "+12%",
                                            "color": "blue"
                                        },
                                        {
                                            "label": "Avg Order Value",
                                            "value": f"${metrics.get('avg_order_value', 0):,.2f}",
                                            "trend": "-3%",
                                            "color": "orange"
                                        },
                                        {
                                            "label": "Customers",
                                            "value": str(metrics.get('total_customers', 0)),
                                            "trend": "+5%",
                                            "color": "purple"
                                        }
                                    ],
                                    "chart": {
                                        "type": "revenue_trend",
                                        "data": [
                                            {"day": "7d ago", "revenue": metrics.get('revenue_last_30_days', 0) * 0.7},
                                            {"day": "6d ago", "revenue": metrics.get('revenue_last_30_days', 0) * 0.75},
                                            {"day": "5d ago", "revenue": metrics.get('revenue_last_30_days', 0) * 0.8},
                                            {"day": "4d ago", "revenue": metrics.get('revenue_last_30_days', 0) * 0.85},
                                            {"day": "3d ago", "revenue": metrics.get('revenue_last_30_days', 0) * 0.9},
                                            {"day": "2d ago", "revenue": metrics.get('revenue_last_30_days', 0) * 0.95},
                                            {"day": "Today", "revenue": metrics.get('revenue_last_30_days', 0)}
                                        ]
                                    }
                                }
                            })
                        
                        if is_last:
                            metadata.update({
                                "tracing_enabled": tracing_enabled,
                                "project": os.getenv("LANGCHAIN_PROJECT"),
                                "run_url": os.getenv("LANGCHAIN_RUN_URL"),
                            })
                        yield StreamChunk(
                            delta=word + " ",
                            done=is_last,
                            metadata=metadata
                        )
                        await asyncio.sleep(0.05)
                else:
                    fallback = self._generate_general_fallback(user_message, business_context)
                    yield StreamChunk(delta=fallback, done=True)
                    
            except Exception as e:
                logger.error(f"LLM error: {e}")
                yield StreamChunk(delta="I'm having trouble right now. Please try again.", done=True)
        
        # Store conversation
        state["messages"].append({"role": "user", "content": user_message})
        if response_text:
            state["messages"].append({"role": "assistant", "content": response_text})
        self.conversations[tenant_id] = state
    
    def _build_general_prompt(self, user_message: str, context: Dict[str, Any]) -> str:
        """Build prompt for general conversation"""
        business_name = context.get("business_name", "your business")
        has_data = context.get("has_data_connected", False)
        metrics = context.get("metrics", {})
        data_sources = context.get("data_sources", {})
        
        prompt = f"""You are a friendly AI business coach for {business_name}.

The user said: "{user_message}"

BUSINESS DATA AVAILABLE:
- Orders: {data_sources.get('orders', 0)} records
- Inventory: {data_sources.get('inventory', 0)} items  
- Customers: {data_sources.get('customers', 0)} records

KEY METRICS:
- Revenue (Last 30 Days): ${metrics.get('revenue_last_30_days', 0):,.2f}
- Orders (Last 30 Days): {metrics.get('orders_last_30_days', 0)}
- Average Order Value: ${metrics.get('avg_order_value', 0):,.2f}
- Total Customers: {metrics.get('total_customers', 0)}
- VIP Customers: {metrics.get('vip_customers', 0)}
- Repeat Customer Rate: {metrics.get('repeat_customer_rate', 0)}%

IMPORTANT: Use these actual numbers in your response! For example:
- "Your revenue over the last 30 days is ${metrics.get('revenue_last_30_days', 0):,.2f} from {metrics.get('orders_last_30_days', 0)} orders"
- "You have {metrics.get('total_customers', 0)} customers with a {metrics.get('repeat_customer_rate', 0)}% repeat rate"
- "Your average order value is ${metrics.get('avg_order_value', 0):,.2f}"

"""
        
        if not has_data:
            prompt += """
⚠️ NOTE: Using sample/test data. Encourage connecting real business data for accurate insights.
"""
        else:
            prompt += """
✅ Using real connected business data.
"""
        
        prompt += """
Respond warmly and helpfully using the specific numbers above. Keep it brief (2-4 sentences). 
Provide actionable insights based on the metrics.
Use emojis sparingly: 💡 🎯 ✨ 📊
"""
        
        return prompt
    
    def _generate_fallback(self, agent_type: str, user_message: str) -> str:
        """Generate fallback response when agent fails"""
        agent_names = {
            "data_analyst": "📊 Data Analyst",
            "data_scientist": "🔬 Data Scientist",
            "goal_analyzer": "🎯 Goal Analyzer",
            "business_consultant": "💼 Business Consultant"
        }
        
        agent_name = agent_names.get(agent_type, "specialist")
        
        return f"I'd love to help with that using our {agent_name}, but I'm having trouble accessing that right now. Could you try asking in a different way, or I can help with something else? 💡"
    
    def _generate_general_fallback(self, user_message: str, context: Dict[str, Any]) -> str:
        """Generate fallback for general conversation"""
        business_name = context.get("business_name", "your business")
        has_data = context.get("has_data_connected", False)
        
        fallback = f"I'm here to help with {business_name}! What would you like to focus on - goals, tasks, data analysis, or performance insights? 💡"
        
        if not has_data:
            fallback += "\n\nPro tip: Connect your business data sources (e-commerce, CRM, accounting) to get personalized insights and recommendations! 📊"
        
        return fallback


# Global instance
_multi_agent_coach: Optional[MultiAgentCoach] = None


def get_multi_agent_coach() -> MultiAgentCoach:
    """Get multi-agent coach instance"""
    global _multi_agent_coach
    if _multi_agent_coach is None:
        _multi_agent_coach = MultiAgentCoach()
    return _multi_agent_coach
