"""
AI Coach Service for SMB Gateway

Provides conversational AI coaching using LLM integration
"""
from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
import logging
import os
import sys

# Add packages to path for LLM import
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from packages.llm import _invoke_llm

logger = logging.getLogger(__name__)


class ChatMessage(BaseModel):
    """Chat message model"""
    role: str  # 'user' or 'assistant'
    content: str
    timestamp: datetime


class ChatRequest(BaseModel):
    """Request for chat completion"""
    message: str = Field(..., min_length=1)
    conversation_history: List[ChatMessage] = Field(default_factory=list)


class ChatResponse(BaseModel):
    """Response from chat completion"""
    message: str
    timestamp: datetime
    context_used: Dict[str, Any] = Field(default_factory=dict)


class CoachService:
    """Service for AI business coach"""
    
    def __init__(self):
        # In-memory conversation storage (replace with database in production)
        self.conversations: Dict[str, List[ChatMessage]] = {}  # {tenant_id: [messages]}
    
    async def chat(
        self,
        tenant_id: str,
        request: ChatRequest,
        business_context: Optional[Dict[str, Any]] = None,
    ) -> ChatResponse:
        """
        Generate AI coach response
        
        Args:
            tenant_id: Tenant identifier
            request: Chat request with user message and history
            business_context: Current business data (goals, health score, tasks, etc.)
        """
        # Build context for LLM
        context = self._build_context(tenant_id, business_context or {})
        
        # Build system prompt
        system_prompt = self._build_system_prompt(context)
        
        # Build conversation history
        messages = self._build_messages(system_prompt, request.conversation_history, request.message)
        
        # Invoke LLM
        response_text = await self._invoke_llm(messages, context)
        
        # Store conversation
        if tenant_id not in self.conversations:
            self.conversations[tenant_id] = []
        
        self.conversations[tenant_id].append(
            ChatMessage(role="user", content=request.message, timestamp=datetime.now())
        )
        self.conversations[tenant_id].append(
            ChatMessage(role="assistant", content=response_text, timestamp=datetime.now())
        )
        
        return ChatResponse(
            message=response_text,
            timestamp=datetime.now(),
            context_used=context,
        )
    
    def get_conversation_history(self, tenant_id: str, limit: int = 50) -> List[ChatMessage]:
        """Get conversation history for a tenant"""
        if tenant_id not in self.conversations:
            return []
        
        return self.conversations[tenant_id][-limit:]
    
    def _build_context(self, tenant_id: str, business_context: Dict[str, Any]) -> Dict[str, Any]:
        """Build context from business data"""
        context = {
            "tenant_id": tenant_id,
            "business_name": business_context.get("business_name", "your business"),
            "industry": business_context.get("industry", "retail"),
        }
        
        # Add health score if available
        if "health_score" in business_context:
            hs = business_context["health_score"]
            context["health_score"] = {
                "overall": hs.get("score", 0),
                "trend": hs.get("trend", 0),
                "revenue_health": hs.get("breakdown", {}).get("revenue", 0),
                "operations_health": hs.get("breakdown", {}).get("operations", 0),
                "customer_health": hs.get("breakdown", {}).get("customer", 0),
            }
        
        # Add goals if available
        if "goals" in business_context:
            goals = business_context["goals"]
            context["active_goals"] = [
                {
                    "title": g.get("title", ""),
                    "category": g.get("category", ""),
                    "progress": round((g.get("current", 0) / g.get("target", 1)) * 100, 1) if g.get("target", 0) > 0 else 0,
                    "current": g.get("current", 0),
                    "target": g.get("target", 0),
                    "unit": g.get("unit", ""),
                }
                for g in goals[:5]  # Top 5 goals
            ]
        
        # Add tasks if available
        if "tasks" in business_context:
            tasks = business_context["tasks"]
            context["pending_tasks"] = [
                {
                    "title": t.get("title", ""),
                    "category": t.get("category", ""),
                    "priority": t.get("priority", "medium"),
                }
                for t in tasks[:5]  # Top 5 tasks
            ]
        
        return context
    
    def _build_system_prompt(self, context: Dict[str, Any]) -> str:
        """Build system prompt with business context"""
        business_name = context.get("business_name", "your business")
        industry = context.get("industry", "retail")
        
        prompt = f"""You are an expert business coach for {business_name}, a {industry} business. 
Your role is to provide actionable, data-driven advice to help the business owner achieve their goals.

Current Business Context:
"""
        
        # Add health score context
        if "health_score" in context:
            hs = context["health_score"]
            prompt += f"""
Business Health Score: {hs['overall']}/100 (Trend: {hs['trend']:+.1f}%)
- Revenue Health: {hs['revenue_health']}/100
- Operations Health: {hs['operations_health']}/100
- Customer Health: {hs['customer_health']}/100
"""
        
        # Add goals context
        if "active_goals" in context and context["active_goals"]:
            prompt += "\nActive Goals:\n"
            for goal in context["active_goals"]:
                prompt += f"- {goal['title']} ({goal['category']}): {goal['current']}/{goal['target']} {goal['unit']} ({goal['progress']:.1f}% complete)\n"
        
        # Add tasks context
        if "pending_tasks" in context and context["pending_tasks"]:
            prompt += "\nPending Tasks:\n"
            for task in context["pending_tasks"]:
                prompt += f"- [{task['priority'].upper()}] {task['title']} ({task['category']})\n"
        
        prompt += """
Guidelines:
1. Be concise and actionable - focus on specific next steps
2. Reference the business data above when relevant
3. Ask clarifying questions when needed
4. Provide specific recommendations based on the business context
5. Be encouraging but realistic
6. Use data from the health score, goals, and tasks to provide personalized advice

Respond in a friendly, professional tone as a trusted business advisor."""
        
        return prompt
    
    def _build_messages(
        self,
        system_prompt: str,
        history: List[ChatMessage],
        user_message: str,
    ) -> List[Dict[str, str]]:
        """Build message array for LLM"""
        messages = [
            {"role": "system", "content": system_prompt}
        ]
        
        # Add conversation history (last 10 messages for context)
        for msg in history[-10:]:
            messages.append({
                "role": msg.role,
                "content": msg.content,
            })
        
        # Add current user message
        messages.append({
            "role": "user",
            "content": user_message,
        })
        
        return messages
    
    async def _invoke_llm(self, messages: List[Dict[str, str]], context: Dict[str, Any]) -> str:
        """
        Invoke LLM to generate response using the actual LLM package
        """
        # Build a single prompt from messages for the LLM
        prompt_parts = []
        for msg in messages:
            role = msg['role'].upper()
            content = msg['content']
            prompt_parts.append(f"{role}: {content}")
        
        full_prompt = "\n\n".join(prompt_parts)
        
        # Add instruction for assistant to respond
        full_prompt += "\n\nASSISTANT:"
        
        logger.info(f"Invoking LLM with prompt length: {len(full_prompt)} characters")
        
        # Invoke the LLM from packages/llm
        try:
            response = _invoke_llm(full_prompt)
            
            if response:
                logger.info(f"LLM response received: {len(response)} characters")
                return response.strip()
            else:
                logger.warning("LLM returned no response, using fallback")
                return self._generate_fallback_response(messages[-1]["content"], context)
                
        except Exception as e:
            logger.error(f"LLM invocation failed: {e}")
            return self._generate_fallback_response(messages[-1]["content"], context)
    
    def _generate_fallback_response(self, user_message: str, context: Dict[str, Any]) -> str:
        """
        Generate fallback response when LLM is unavailable
        """
        user_message_lower = user_message.lower()
        
        # Template-based responses for common queries as fallback
        
        if "health" in user_message_lower or "score" in user_message_lower:
            if "health_score" in context:
                hs = context["health_score"]
                if hs["overall"] >= 80:
                    return f"Your business health is strong at {hs['overall']}/100! Focus on maintaining momentum in revenue ({hs['revenue_health']}/100) and operations ({hs['operations_health']}/100). Consider setting stretch goals to push further."
                elif hs["overall"] >= 60:
                    return f"Your health score of {hs['overall']}/100 shows solid performance with room for improvement. I recommend focusing on your weakest area: {'revenue' if hs['revenue_health'] < 70 else 'operations' if hs['operations_health'] < 70 else 'customer retention'}. What specific challenges are you facing?"
                else:
                    return f"Your health score of {hs['overall']}/100 indicates areas needing attention. Let's prioritize: revenue health is at {hs['revenue_health']}/100. I suggest reviewing your sales funnel and promotional strategies. Would you like specific tactics?"
            return "I'd be happy to discuss your business health. Could you share more details about your current performance?"
        
        elif "goal" in user_message_lower:
            if "active_goals" in context and context["active_goals"]:
                goals = context["active_goals"]
                in_progress = [g for g in goals if 20 <= g["progress"] < 80]
                if in_progress:
                    goal = in_progress[0]
                    return f"Let's focus on '{goal['title']}' - you're {goal['progress']:.0f}% there! To reach your target of {goal['target']} {goal['unit']}, you need {goal['target'] - goal['current']:.0f} more {goal['unit']}. What obstacles are slowing progress?"
                return f"You have {len(goals)} active goals. The highest priority is '{goals[0]['title']}' ({goals[0]['progress']:.0f}% complete). Want to discuss strategies to accelerate this?"
            return "Setting clear goals is crucial. What business outcomes would you like to achieve in the next 30-90 days?"
        
        elif "task" in user_message_lower or "todo" in user_message_lower:
            if "pending_tasks" in context and context["pending_tasks"]:
                tasks = context["pending_tasks"]
                high_priority = [t for t in tasks if t["priority"] in ["high", "urgent"]]
                if high_priority:
                    return f"You have {len(high_priority)} high-priority tasks. Start with '{high_priority[0]['title']}' - this will have the most impact. Need help breaking it down into smaller steps?"
                return f"I see {len(tasks)} tasks on your list. '{tasks[0]['title']}' looks like a good starting point. Shall we tackle that together?"
            return "It sounds like you're looking for action items. Based on your goals, I can suggest specific tasks. What area would you like to focus on first?"
        
        elif any(word in user_message_lower for word in ["help", "stuck", "challenge", "problem"]):
            return "I'm here to help! To give you the best advice, I need to understand your specific challenge. Is this related to sales, operations, customer retention, or something else? Share more details and I'll provide targeted recommendations."
        
        elif any(word in user_message_lower for word in ["hello", "hi", "hey"]):
            business_name = context.get("business_name", "your business")
            return f"Hello! I'm your AI business coach for {business_name}. I'm here to help you achieve your goals and improve your business performance. What would you like to discuss today?"
        
        else:
            # Default response
            return "That's a great question! Based on your business data, I'd recommend focusing on your key priorities: goals, critical tasks, and areas where your health score needs improvement. What specific aspect would you like to explore?"


# Global instance
_coach_service = None

def get_coach_service() -> CoachService:
    """Get coach service instance"""
    global _coach_service
    if _coach_service is None:
        _coach_service = CoachService()
    return _coach_service
