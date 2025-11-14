"""
Goal Planner Agent - LangGraph Implementation

Decomposes user goals into SMART goals using multi-agent workflow.
"""

from __future__ import annotations

import logging
from typing import Any, TypedDict, Annotated, Sequence
from datetime import datetime, timedelta

from langgraph.graph import StateGraph, END
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate

from backend.services.coach.llm_router import get_llm_router

logger = logging.getLogger(__name__)


class GoalPlannerState(TypedDict):
    """State for goal planning workflow."""
    messages: Annotated[Sequence[BaseMessage], "Conversation history"]
    user_goal: str
    context: dict[str, Any]
    smart_goals: list[dict[str, Any]]
    current_metrics: dict[str, float]
    industry_benchmarks: dict[str, float]
    next_step: str


class GoalPlannerAgent:
    """
    Multi-agent workflow for decomposing goals into SMART goals.
    
    Workflow:
    1. Extract intent from user goal
    2. Gather relevant context (metrics, benchmarks)
    3. Generate SMART sub-goals
    4. Validate goals (Specific, Measurable, Achievable, Relevant, Time-bound)
    5. Return structured goal plan
    """
    
    def __init__(self):
        """Initialize goal planner with LangGraph workflow."""
        self.llm_router = get_llm_router()
        self.graph = self._build_graph()
    
    def _build_graph(self) -> StateGraph:
        """Build LangGraph workflow."""
        workflow = StateGraph(GoalPlannerState)
        
        # Add nodes
        workflow.add_node("extract_intent", self._extract_intent)
        workflow.add_node("gather_context", self._gather_context)
        workflow.add_node("generate_goals", self._generate_goals)
        workflow.add_node("validate_goals", self._validate_goals)
        
        # Define edges
        workflow.set_entry_point("extract_intent")
        workflow.add_edge("extract_intent", "gather_context")
        workflow.add_edge("gather_context", "generate_goals")
        workflow.add_edge("generate_goals", "validate_goals")
        workflow.add_edge("validate_goals", END)
        
        return workflow.compile()
    
    async def _extract_intent(self, state: GoalPlannerState) -> GoalPlannerState:
        """Extract user intent and goal category."""
        logger.info("Extracting intent from user goal")
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a business goal analyst. Extract the following from the user's goal:
1. Primary metric to improve (revenue, cost, customer satisfaction, etc.)
2. Target direction (increase, decrease, maintain)
3. Timeframe (if mentioned)
4. Current pain points or constraints

Respond in JSON format:
{
  "metric": "revenue",
  "direction": "increase",
  "timeframe": "6 months",
  "pain_points": ["low customer retention", "seasonal demand"]
}"""),
            ("user", "{goal}")
        ])
        
        response = await self.llm_router.generate(
            query=prompt.format(goal=state["user_goal"]),
            context={"requires_calculation": False}
        )
        
        # Parse intent (simple implementation)
        intent = {
            "metric": "revenue",  # Default, should parse from response
            "direction": "increase",
            "timeframe": "90 days"
        }
        
        state["context"]["intent"] = intent
        state["messages"].append(AIMessage(content=f"Intent extracted: {intent}"))
        
        return state
    
    async def _gather_context(self, state: GoalPlannerState) -> GoalPlannerState:
        """Gather relevant metrics and benchmarks."""
        logger.info("Gathering context (metrics, benchmarks)")
        
        # In real implementation, query database
        # For now, use placeholder data
        state["current_metrics"] = {
            "monthly_revenue": 50000.0,
            "customer_count": 150,
            "avg_order_value": 333.33,
            "churn_rate": 0.15
        }
        
        state["industry_benchmarks"] = {
            "revenue_growth_rate": 0.15,  # 15% annual
            "avg_order_value": 400.0,
            "churn_rate": 0.10
        }
        
        state["messages"].append(AIMessage(content="Context gathered"))
        return state
    
    async def _generate_goals(self, state: GoalPlannerState) -> GoalPlannerState:
        """Generate SMART sub-goals."""
        logger.info("Generating SMART goals")
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a SMART goal generator for SMBs. 

Given:
- User goal: {user_goal}
- Current metrics: {metrics}
- Industry benchmarks: {benchmarks}

Generate 3-5 SMART goals that decompose the user's goal into actionable sub-goals.

Each goal must be:
- **Specific**: Clear and well-defined
- **Measurable**: Quantifiable metric
- **Achievable**: Realistic given current metrics
- **Relevant**: Aligned with user's intent
- **Time-bound**: Specific deadline

Format as JSON array:
[
  {{
    "title": "Increase monthly revenue to $60,000",
    "metric": "monthly_revenue",
    "target_value": 60000,
    "current_value": 50000,
    "unit": "$",
    "deadline": "2026-02-14",
    "category": "revenue",
    "description": "Achieve 20% revenue growth through new customer acquisition and upselling",
    "success_criteria": ["Revenue reaches $60k", "Growth is sustainable"]
  }}
]"""),
            ("user", "User goal: {user_goal}")
        ])
        
        response = await self.llm_router.generate(
            query=prompt.format(
                user_goal=state["user_goal"],
                metrics=state["current_metrics"],
                benchmarks=state["industry_benchmarks"]
            ),
            context={"requires_calculation": True}
        )
        
        # Parse goals (simplified - should parse JSON from response)
        deadline = datetime.now() + timedelta(days=90)
        state["smart_goals"] = [
            {
                "title": "Increase monthly revenue by 20%",
                "metric": "monthly_revenue",
                "target_value": 60000,
                "current_value": 50000,
                "unit": "$",
                "deadline": deadline.isoformat(),
                "category": "revenue",
                "description": "Achieve through customer acquisition and retention",
                "parent_goal_id": None
            },
            {
                "title": "Reduce customer churn to 10%",
                "metric": "churn_rate",
                "target_value": 0.10,
                "current_value": 0.15,
                "unit": "%",
                "deadline": deadline.isoformat(),
                "category": "customer",
                "description": "Improve retention through better service",
                "parent_goal_id": None
            },
            {
                "title": "Increase average order value to $400",
                "metric": "avg_order_value",
                "target_value": 400,
                "current_value": 333.33,
                "unit": "$",
                "deadline": deadline.isoformat(),
                "category": "revenue",
                "description": "Upsell and cross-sell strategies",
                "parent_goal_id": None
            }
        ]
        
        state["messages"].append(AIMessage(
            content=f"Generated {len(state['smart_goals'])} SMART goals"
        ))
        
        return state
    
    async def _validate_goals(self, state: GoalPlannerState) -> GoalPlannerState:
        """Validate goals meet SMART criteria."""
        logger.info("Validating SMART goals")
        
        validated_goals = []
        for goal in state["smart_goals"]:
            # Check SMART criteria
            is_valid = (
                goal.get("title") and
                goal.get("metric") and
                goal.get("target_value") is not None and
                goal.get("deadline")
            )
            
            if is_valid:
                # Check achievability (target within 2x current)
                if goal.get("current_value"):
                    ratio = goal["target_value"] / goal["current_value"]
                    if goal["unit"] == "%":
                        is_achievable = 0.5 <= ratio <= 2.0
                    else:
                        is_achievable = 0.5 <= ratio <= 3.0
                    
                    if is_achievable:
                        validated_goals.append(goal)
                        logger.info(f"✓ Goal validated: {goal['title']}")
                    else:
                        logger.warning(f"✗ Goal unrealistic: {goal['title']} (ratio: {ratio:.2f})")
                else:
                    validated_goals.append(goal)
        
        state["smart_goals"] = validated_goals
        state["messages"].append(AIMessage(
            content=f"Validated {len(validated_goals)} goals"
        ))
        
        return state
    
    async def plan(self, user_goal: str, context: dict[str, Any] = None) -> dict[str, Any]:
        """
        Plan SMART goals from user input.
        
        Args:
            user_goal: User's high-level goal
            context: Optional context (tenant_id, user_id, etc.)
        
        Returns:
            Dict with smart_goals list and planning metadata
        """
        logger.info(f"Planning goals for: {user_goal}")
        
        initial_state: GoalPlannerState = {
            "messages": [HumanMessage(content=user_goal)],
            "user_goal": user_goal,
            "context": context or {},
            "smart_goals": [],
            "current_metrics": {},
            "industry_benchmarks": {},
            "next_step": ""
        }
        
        # Run workflow
        final_state = await self.graph.ainvoke(initial_state)
        
        return {
            "goals": final_state["smart_goals"],
            "current_metrics": final_state["current_metrics"],
            "benchmarks": final_state["industry_benchmarks"],
            "intent": final_state["context"].get("intent", {}),
            "messages": [msg.content for msg in final_state["messages"]]
        }


# Global agent instance
_agent: GoalPlannerAgent | None = None


def get_goal_planner() -> GoalPlannerAgent:
    """Get or create global goal planner agent."""
    global _agent
    if _agent is None:
        _agent = GoalPlannerAgent()
    return _agent
