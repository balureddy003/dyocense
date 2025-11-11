"""
Enhanced Conversational AI Coach with LangGraph

Provides streaming, context-aware business coaching with multi-turn conversations
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
from .coach_service import ChatMessage  # Use shared ChatMessage model

logger = logging.getLogger(__name__)

# Try to import langgraph if available, otherwise use simple state machine
try:
    from langgraph.graph import StateGraph, END
    from langgraph.checkpoint.memory import MemorySaver
    LANGGRAPH_AVAILABLE = True
except ImportError:
    logger.warning("LangGraph not available, using simple state machine")
    LANGGRAPH_AVAILABLE = False
    StateGraph = None
    END = "END"


class StreamChunk(BaseModel):
    """Streaming response chunk"""
    delta: str  # Incremental text
    done: bool = False
    metadata: Dict[str, Any] = Field(default_factory=dict)


class AgentState(TypedDict):
    """State for the conversational agent"""
    messages: List[Dict[str, str]]
    business_context: Dict[str, Any]
    current_intent: Optional[str]
    conversation_stage: str  # 'greeting', 'understanding', 'advising', 'follow_up'
    user_profile: Dict[str, Any]
    action_plan: List[str]


class ConversationalCoachAgent:
    """LangGraph-based conversational AI coach"""
    
    def __init__(self):
        self.conversations: Dict[str, AgentState] = {}
        
        if LANGGRAPH_AVAILABLE:
            self.graph = self._build_graph()
            self.checkpointer = MemorySaver()
        else:
            self.graph = None
    
    def _build_graph(self):
        """Build LangGraph conversation graph"""
        if not LANGGRAPH_AVAILABLE or StateGraph is None:  # type: ignore[truthy-function]
            return None
        
        # Define the graph
        workflow = StateGraph(AgentState)  # type: ignore[operator]
        
        # Add nodes
        workflow.add_node("analyze_intent", self._analyze_intent)
        workflow.add_node("gather_context", self._gather_context)
        workflow.add_node("generate_response", self._generate_response)
        workflow.add_node("suggest_actions", self._suggest_actions)
        
        # Define edges
        workflow.set_entry_point("analyze_intent")
        
        workflow.add_conditional_edges(
            "analyze_intent",
            self._route_based_on_intent,
            {
                "context_needed": "gather_context",
                "direct_response": "generate_response",
                "action_planning": "suggest_actions"
            }
        )
        
        workflow.add_edge("gather_context", "generate_response")
        workflow.add_edge("suggest_actions", "generate_response")
        workflow.add_edge("generate_response", END)
        
        return workflow.compile()
    
    async def _analyze_intent(self, state: AgentState) -> AgentState:
        """Analyze user intent"""
        last_message = state["messages"][-1]["content"].lower()
        
        # Intent classification
        if any(word in last_message for word in ["connect", "data", "integrate", "source", "connection", "connector"]):
            intent = "data_connection"
        elif any(word in last_message for word in ["goal", "target", "achieve", "plan"]):
            intent = "goal_discussion"
        elif any(word in last_message for word in ["task", "todo", "action", "step"]):
            intent = "task_management"
        elif any(word in last_message for word in ["health", "score", "performance", "metric"]):
            intent = "performance_analysis"
        elif any(word in last_message for word in ["help", "how", "what", "why", "suggest"]):
            intent = "seeking_advice"
        elif any(word in last_message for word in ["hello", "hi", "hey", "start"]):
            intent = "greeting"
        else:
            intent = "general_inquiry"
        
        state["current_intent"] = intent
        logger.info(f"Detected intent: {intent}")
        return state
    
    def _route_based_on_intent(self, state: AgentState) -> str:
        """Route conversation based on intent"""
        intent = state.get("current_intent", "general_inquiry")
        
        if intent in ["goal_discussion", "task_management", "performance_analysis"]:
            return "context_needed"
        elif intent == "seeking_advice":
            return "action_planning"
        else:
            return "direct_response"
    
    async def _gather_context(self, state: AgentState) -> AgentState:
        """Gather relevant business context"""
        context = state.get("business_context", {})
        intent = state.get("current_intent")
        
        # Add relevant context based on intent
        if intent == "goal_discussion" and "goals" in context:
            state["conversation_stage"] = "advising"
        elif intent == "task_management" and "tasks" in context:
            state["conversation_stage"] = "advising"
        elif intent == "performance_analysis" and "health_score" in context:
            state["conversation_stage"] = "advising"
        
        return state
    
    async def _suggest_actions(self, state: AgentState) -> AgentState:
        """Suggest actionable steps"""
        context = state.get("business_context", {})
        actions = []
        
        # Generate action suggestions based on context
        if "health_score" in context:
            hs = context["health_score"]
            if hs.get("overall", 0) < 70:
                if hs.get("breakdown", {}).get("revenue", 0) < 70:
                    actions.append("Review pricing strategy and promotional campaigns")
                if hs.get("breakdown", {}).get("operations", 0) < 70:
                    actions.append("Optimize inventory management and reduce stockouts")
                if hs.get("breakdown", {}).get("customer", 0) < 70:
                    actions.append("Implement customer retention program")
        
        if "active_goals" in context:
            goals = context["active_goals"]
            behind_goals = [g for g in goals if g.get("progress", 0) < 30]
            if behind_goals:
                actions.append(f"Focus on goal: {behind_goals[0].get('title', 'unnamed goal')}")
        
        state["action_plan"] = actions
        return state
    
    async def _generate_response(self, state: AgentState) -> AgentState:
        """Generate conversational response"""
        # This is handled in the streaming method
        return state
    
    def _build_conversational_prompt(self, state: AgentState) -> str:
        """Build a conversational, context-aware prompt"""
        context = state.get("business_context", {})
        intent = state.get("current_intent", "general")
        stage = state.get("conversation_stage", "understanding")
        
        business_name = context.get("business_name", "your business")
        has_data_connected = context.get("has_data_connected", False)
        
        # Build personality and tone
        prompt = f"""You are a friendly, knowledgeable AI business coach having a natural conversation with the owner of {business_name}.

CONVERSATIONAL STYLE:
- Be warm, encouraging, and personal (use "you" and "your")
- Ask follow-up questions to understand their situation better
- Show genuine interest in their challenges and wins
- Break down complex topics into simple, actionable advice
- Use examples and analogies when helpful
- Celebrate progress and provide constructive guidance

DATA CONNECTION STATUS:
"""
        
        # Check if data is connected
        if not has_data_connected:
            data_sources = context.get("data_sources", {})
            prompt += f"""⚠️ NO REAL DATA CONNECTED
The user has not connected their business data sources yet.
- Orders: {data_sources.get('orders', 0)} (sample data)
- Inventory: {data_sources.get('inventory', 0)} (sample data)
- Customers: {data_sources.get('customers', 0)} (sample data)

IMPORTANT: You should gently encourage them to connect their real business data to get personalized insights.
Explain that connecting data sources like:
- E-commerce platform (Shopify, WooCommerce, GrandNode)
- CRM (Salesforce, HubSpot)
- Accounting software (QuickBooks, Xero)

Will enable you to provide:
✨ Real-time business health monitoring
📊 Accurate revenue and sales analytics
🎯 Personalized recommendations based on their actual data
📈 Trend analysis and forecasting
💡 Proactive alerts about opportunities and issues

Keep this friendly and helpful, not pushy. Frame it as unlocking better insights.
"""
        else:
            data_sources = context.get("data_sources", {})
            prompt += f"""✅ DATA CONNECTED
- Orders: {data_sources.get('orders', 0)}
- Inventory: {data_sources.get('inventory', 0)}
- Customers: {data_sources.get('customers', 0)}
"""
        
        prompt += "\nCURRENT CONTEXT:\n"
        
        # Add health score context
        if "health_score" in context:
            hs = context["health_score"]
            prompt += f"""
Business Health: {hs.get('overall', 0)}/100 (Trend: {hs.get('trend', 0):+.1f}%)
- Revenue: {hs.get('breakdown', {}).get('revenue', 0)}/100
- Operations: {hs.get('breakdown', {}).get('operations', 0)}/100
- Customer: {hs.get('breakdown', {}).get('customer', 0)}/100
"""
        
        # Add goals context
        if "active_goals" in context and context["active_goals"]:
            prompt += "\nCurrent Goals:\n"
            for goal in context["active_goals"][:3]:
                progress = goal.get("progress", 0)
                emoji = "🎯" if progress > 70 else "⚡" if progress > 30 else "🔥"
                prompt += f"{emoji} {goal.get('title', 'Unknown')}: {progress:.0f}% complete ({goal.get('current', 0)}/{goal.get('target', 0)} {goal.get('unit', '')})\n"
        
        # Add tasks context
        if "pending_tasks" in context and context["pending_tasks"]:
            prompt += "\nUpcoming Tasks:\n"
            for task in context["pending_tasks"][:3]:
                priority_emoji = "🔴" if task.get("priority") == "high" else "🟡" if task.get("priority") == "medium" else "🟢"
                prompt += f"{priority_emoji} {task.get('title', 'Unknown')} ({task.get('category', 'General')})\n"
        
        # Add action plan if available
        if state.get("action_plan"):
            prompt += "\nSuggested Actions:\n"
            for action in state["action_plan"]:
                prompt += f"• {action}\n"
        
        # Add conversation guidance based on intent
        if intent == "greeting":
            prompt += "\nThe user is greeting you. Respond warmly and ask what they'd like to focus on today.\n"
        elif intent == "data_connection":
            prompt += "\nThe user is asking about data connections. Explain the benefits and available integrations (e-commerce, CRM, accounting). Be encouraging but not pushy.\n"
        elif intent == "goal_discussion":
            prompt += "\nThe user wants to discuss goals. Reference their current goals and offer specific strategies to accelerate progress.\n"
        elif intent == "task_management":
            prompt += "\nThe user needs help with tasks. Suggest prioritization or break down complex tasks.\n"
        elif intent == "performance_analysis":
            prompt += "\nThe user wants to understand their performance. Analyze the health score and provide insights.\n"
        elif intent == "seeking_advice":
            prompt += "\nThe user is seeking advice. Provide actionable recommendations based on their data.\n"
        
        prompt += """
RESPONSE GUIDELINES:
1. Keep responses conversational and concise (2-4 sentences usually)
2. Reference specific data from their business when relevant
3. Ask ONE thoughtful follow-up question if appropriate
4. Use emojis sparingly but effectively (💡🎯📊✨)
5. Be specific - use numbers, percentages, and concrete examples
6. End with encouragement or a clear next step

Now respond naturally to the conversation."""
        
        return prompt
    
    async def stream_response(
        self,
        tenant_id: str,
        user_message: str,
        business_context: Dict[str, Any],
        conversation_history: List[ChatMessage]
    ) -> AsyncGenerator[StreamChunk, None]:
        """Stream conversational response with SSE"""
        
        # Initialize or get conversation state
        if tenant_id not in self.conversations:
            self.conversations[tenant_id] = AgentState(
                messages=[],
                business_context=business_context,
                current_intent=None,
                conversation_stage="greeting",
                user_profile={},
                action_plan=[]
            )
        
        state = self.conversations[tenant_id]
        state["business_context"] = business_context
        
        # Add message history
        state["messages"] = [
            {"role": msg.role, "content": msg.content}
            for msg in conversation_history[-10:]  # Last 10 messages
        ]
        state["messages"].append({"role": "user", "content": user_message})
        
        # Run through graph if available
        if LANGGRAPH_AVAILABLE and self.graph:
            try:
                state = await self._run_graph(state)
            except Exception as e:
                logger.error(f"Graph execution error: {e}")
        else:
            # Simple intent analysis fallback
            state = await self._analyze_intent(state)
            if state["current_intent"] in ["goal_discussion", "task_management", "performance_analysis"]:
                state = await self._gather_context(state)
            if state["current_intent"] == "seeking_advice":
                state = await self._suggest_actions(state)
        
        # Build conversational prompt
        system_prompt = self._build_conversational_prompt(state)
        
        # Build messages for LLM
        messages = [
            {"role": "system", "content": system_prompt}
        ]
        messages.extend(state["messages"][-5:])  # Last 5 messages for context
        
        # Convert to single prompt
        full_prompt = "\n\n".join([
            f"{msg['role'].upper()}: {msg['content']}"
            for msg in messages
        ])
        full_prompt += "\n\nASSISTANT:"
        
        logger.info(f"Streaming response for tenant {tenant_id}")
        
        # Local run logging (import locally to avoid circular import at module load)
        try:
            from .run_logs import create_run as _create_runlog, append_output as _append_output, finalize_run as _finalize_run
            run_id = _create_runlog(tenant_id, user_message, metadata={"source": "conversational_coach"})
        except Exception:
            run_id = None

        try:
            # Call LLM
            response_text = _invoke_llm(full_prompt)
            
            if response_text:
                # Simulate streaming by chunking the response
                words = response_text.split()
                current_chunk = ""
                tracing_enabled = os.getenv("LANGCHAIN_TRACING_V2", "").lower() == "true"
                
                for i, word in enumerate(words):
                    current_chunk += word + " "
                    
                    # Yield chunks at natural boundaries
                    if len(current_chunk) > 30 or i == len(words) - 1:
                        is_last = (i == len(words) - 1)
                        metadata = {
                            "intent": state.get("current_intent"),
                            "stage": state.get("conversation_stage")
                        }
                        if is_last:
                            metadata.update({
                                "tracing_enabled": tracing_enabled,
                                "project": os.getenv("LANGCHAIN_PROJECT"),
                                "run_url": os.getenv("LANGCHAIN_RUN_URL"),
                            })
                        # Append to run log
                        if run_id:
                            try:
                                _append_output(tenant_id, run_id, current_chunk)
                            except Exception:
                                pass
                        if is_last and run_id:
                            try:
                                finalized = _finalize_run(tenant_id, run_id, metadata={"intent": state.get("current_intent")})
                                if finalized:
                                    metadata.setdefault("run_url", f"/v1/tenants/{tenant_id}/coach/runs/{run_id}")
                            except Exception:
                                pass
                        yield StreamChunk(delta=current_chunk, done=is_last, metadata=metadata)
                        current_chunk = ""
                        await asyncio.sleep(0.05)  # Small delay for streaming effect
            else:
                # Fallback response
                fallback = self._generate_fallback_response(user_message, business_context)
                yield StreamChunk(delta=fallback, done=True)
                
        except Exception as e:
            logger.error(f"Streaming error: {e}")
            error_msg = "I apologize, but I'm having trouble processing that right now. Could you rephrase your question?"
            yield StreamChunk(delta=error_msg, done=True)
        
        # Store conversation
        state["messages"].append({"role": "assistant", "content": response_text or ""})
        self.conversations[tenant_id] = state
    
    async def _run_graph(self, state: AgentState) -> AgentState:
        """Run the LangGraph"""
        if not LANGGRAPH_AVAILABLE or not self.graph:
            return state
        try:
            result = await self.graph.ainvoke(state)  # type: ignore[attr-defined]
            # Ensure we return a dict matching AgentState expectations; fall back to original state otherwise
            if isinstance(result, dict):
                # Merge result onto state to retain required keys
                merged: AgentState = state.copy()  # type: ignore
                merged.update(result)  # type: ignore
                return merged
            return state
        except Exception as e:
            logger.error(f"LangGraph invocation failed, falling back to original state: {e}")
            return state
    
    def _generate_fallback_response(self, user_message: str, context: Dict[str, Any]) -> str:
        """Generate fallback response"""
        msg_lower = user_message.lower()
        
        # Check if data is connected
        has_data_connected = context.get("has_data_connected", False)
        
        # If no data connected, prioritize encouraging data connection
        if not has_data_connected and any(word in msg_lower for word in ["help", "insight", "advice", "improve", "better", "analyze", "how"]):
            return (
                "I'd love to help you with personalized insights! 💡 To give you the most accurate advice, "
                "I recommend connecting your business data sources (like your e-commerce platform or CRM). "
                "This will help me understand your revenue trends, inventory levels, and customer behavior. "
                "Would you like to know more about connecting your data? 📊"
            )
        
        if "goal" in msg_lower:
            if context.get("active_goals"):
                goal = context["active_goals"][0]
                return f"Let's talk about your goal: {goal['title']}. You're at {goal['progress']:.0f}% - what's been your biggest challenge so far?"
            return "What kind of business goal would you like to set? Revenue, customer acquisition, or operational efficiency?"
        
        if "health" in msg_lower or "score" in msg_lower:
            if context.get("health_score"):
                score = context["health_score"]["overall"]
                if not has_data_connected:
                    return (
                        f"Your current health score is {score}/100 based on sample data. "
                        "For real-time insights based on your actual business, I recommend connecting your data sources. "
                        "This will give you accurate revenue tracking, inventory alerts, and customer insights! 📈"
                    )
                return f"Your health score is {score}/100. What specific area would you like to improve - revenue, operations, or customer satisfaction?"
            return "I'd love to analyze your business health. What metrics are you most concerned about?"
        
        if any(word in msg_lower for word in ["connect", "data", "integrate", "source"]):
            return (
                "Great question! 🎯 You can connect various data sources to get personalized insights:\n\n"
                "📦 E-commerce: Shopify, WooCommerce, GrandNode\n"
                "👥 CRM: Salesforce, HubSpot\n"
                "💰 Accounting: QuickBooks, Xero\n\n"
                "Once connected, I can provide real-time analytics, trend analysis, and proactive recommendations "
                "based on your actual business data. Would you like help getting started?"
            )
        
        business_name = context.get("business_name", "your business")
        
        if not has_data_connected:
            return (
                f"I'm here to help with {business_name}! 👋 "
                "For the best experience, I recommend connecting your business data sources first. "
                "This will unlock personalized insights, real-time analytics, and accurate recommendations. "
                "What would you like to explore - data integration, goals, or current insights? 💡"
            )
        
        return f"I'm here to help with {business_name}! What would you like to focus on - goals, tasks, or performance insights? 💡"


# Global instance
_coach_agent: Optional[ConversationalCoachAgent] = None


def get_conversational_coach() -> ConversationalCoachAgent:
    """Get conversational coach agent instance"""
    global _coach_agent
    if _coach_agent is None:
        _coach_agent = ConversationalCoachAgent()
    return _coach_agent
