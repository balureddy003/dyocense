"""
Multi-Agent System using LangGraph for business goal decomposition and analysis.

Architecture:
- Orchestrator: Coordinates agent handoffs and maintains conversation state
- Goal Analyzer: Breaks down business goals into SMART objectives
- Data Analyst: Analyzes data availability and quality
- Data Scientist: Builds models, forecasts, and optimization solutions
- Business Consultant: Provides strategic recommendations and action plans
"""

from __future__ import annotations

import json
import logging
from typing import TypedDict, Annotated, List, Dict, Any, Optional, Literal
from dataclasses import dataclass, field
import operator

try:
    from langgraph.graph import StateGraph, END
    from langgraph.prebuilt import ToolNode
    from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, BaseMessage
    from langchain_openai import ChatOpenAI, AzureChatOpenAI
    LANGGRAPH_AVAILABLE = True
except ImportError:
    LANGGRAPH_AVAILABLE = False
    StateGraph = None
    ToolNode = None
    BaseMessage = None

try:
    from .mcp_tools import get_available_mcp_tools, execute_mcp_tool, get_tenant_connectors
    MCP_TOOLS_AVAILABLE = True
except ImportError:
    MCP_TOOLS_AVAILABLE = False
    logger.warning("MCP tools not available")

logger = logging.getLogger(__name__)


# Agent State Definition
class AgentState(TypedDict):
    """State shared across all agents in the multi-agent system."""
    messages: Annotated[List[BaseMessage], operator.add]
    user_goal: str
    current_agent: str
    tenant_id: Optional[str]  # Added for tenant-specific connector access
    available_connectors: Optional[List[str]]  # ERPNext, CSV, etc.
    goal_analysis: Optional[Dict[str, Any]]
    data_analysis: Optional[Dict[str, Any]]
    model_results: Optional[Dict[str, Any]]
    recommendations: Optional[Dict[str, Any]]
    next_agent: Optional[str]
    final_response: Optional[str]
    iteration_count: int
    max_iterations: int


@dataclass
class Agent:
    """Base class for specialized agents."""
    name: str
    role: str
    capabilities: List[str]
    system_prompt: str
    llm: Any = None
    
    def __post_init__(self):
        """Initialize LLM for the agent."""
        if not LANGGRAPH_AVAILABLE:
            logger.warning("LangGraph not available, agent will use fallback mode")
            return
            
        # This will be configured by the orchestrator
        self.llm = None
    
    def invoke(self, state: AgentState) -> Dict[str, Any]:
        """Execute agent logic and return updated state."""
        raise NotImplementedError("Subclasses must implement invoke()")


class GoalAnalyzerAgent(Agent):
    """Analyzes and decomposes business goals into actionable objectives."""
    
    def __init__(self):
        super().__init__(
            name="goal_analyzer",
            role="Goal Analyzer",
            capabilities=[
                "SMART goal validation",
                "Goal decomposition",
                "Success criteria definition",
                "Timeline estimation"
            ],
            system_prompt="""You are a Goal Analyzer agent specializing in business objective analysis.

Your responsibilities:
1. Analyze the user's business goal for clarity and specificity
2. Break down vague goals into SMART objectives (Specific, Measurable, Achievable, Relevant, Time-bound)
3. Identify required data sources and metrics
4. Define success criteria and KPIs
5. Estimate timeline and milestones

When analyzing a goal:
- Ask clarifying questions if the goal is too vague
- Identify the primary metric (revenue, cost, efficiency, etc.)
- Determine the target value and timeframe
- List constraints and assumptions
- Identify data requirements

Output a structured goal analysis with:
- refined_goal: Clear SMART goal statement
- primary_metric: Main KPI to track
- target_value: Quantifiable target
- timeframe: Timeline for achievement
- success_criteria: List of success indicators
- data_needed: Required data sources
- assumptions: Key assumptions made
- next_steps: What the data analyst should focus on"""
        )
    
    def invoke(self, state: AgentState) -> Dict[str, Any]:
        """Analyze the business goal."""
        if not self.llm:
            return self._fallback_analysis(state)
        
        messages = state["messages"] + [
            SystemMessage(content=self.system_prompt),
            HumanMessage(content=f"Analyze this business goal: {state['user_goal']}")
        ]
        
        response = self.llm.invoke(messages)
        
        # Parse the response to extract structured goal analysis
        goal_analysis = self._parse_goal_analysis(response.content)
        
        return {
            "messages": [AIMessage(content=response.content, name=self.name)],
            "current_agent": self.name,
            "goal_analysis": goal_analysis,
            "next_agent": "data_analyst" if goal_analysis.get("data_needed") else "business_consultant"
        }
    
    def _parse_goal_analysis(self, content: str) -> Dict[str, Any]:
        """Extract structured data from agent response."""
        # Try to extract JSON if present
        if "```json" in content:
            json_start = content.find("```json") + 7
            json_end = content.find("```", json_start)
            try:
                return json.loads(content[json_start:json_end])
            except:
                pass
        
        # Fallback: create structure from text
        return {
            "refined_goal": state.get("user_goal", ""),
            "analysis": content,
            "data_needed": True  # Assume data is needed
        }
    
    def _fallback_analysis(self, state: AgentState) -> Dict[str, Any]:
        """Fallback when LangGraph not available."""
        goal = state["user_goal"]
        analysis = {
            "refined_goal": goal,
            "primary_metric": "business performance",
            "data_needed": True,
            "analysis": f"Goal requires data analysis: {goal}"
        }
        
        return {
            "messages": [AIMessage(content=f"Analyzing goal: {goal}", name=self.name)],
            "goal_analysis": analysis,
            "next_agent": "data_analyst"
        }


class DataAnalystAgent(Agent):
    """Analyzes data availability, quality, and prepares datasets."""
    
    def __init__(self):
        super().__init__(
            name="data_analyst",
            role="Data Analyst",
            capabilities=[
                "Data source identification",
                "Data quality assessment",
                "Dataset preparation",
                "Feature engineering",
                "Data visualization"
            ],
            system_prompt="""You are a Data Analyst agent specializing in business data analysis.

Your responsibilities:
1. Assess available data sources and their relevance to the goal
2. Evaluate data quality (completeness, accuracy, timeliness)
3. Identify missing data and gaps
4. Recommend data connections (CRM, ERP, spreadsheets, etc.)
5. Prepare datasets for modeling

When analyzing data requirements:
- Map goal metrics to available data fields
- Check for sufficient historical data
- Identify seasonality or trends
- Assess data freshness and update frequency
- Calculate basic statistics and distributions

Output format:
- available_data: List of connected data sources with metadata
- data_quality: Assessment of each source
- missing_data: Gaps that need to be filled
- recommended_connectors: Specific systems to connect
- data_summary: Key statistics and insights
- ready_for_modeling: Boolean flag
- next_steps: What the data scientist should do

Use markers in your response:
- [SHOW_CONNECTORS: crm, accounting] to suggest connectors
- [SHOW_UPLOADER: csv] to request file uploads"""
        )
    
    def invoke(self, state: AgentState) -> Dict[str, Any]:
        """Analyze data availability and quality."""
        if not self.llm:
            return self._fallback_data_analysis(state)
        
        goal_analysis = state.get("goal_analysis", {})
        
        messages = state["messages"] + [
            SystemMessage(content=self.system_prompt),
            HumanMessage(content=f"""Analyze data requirements for this goal:

Goal: {goal_analysis.get('refined_goal', state['user_goal'])}
Required Metrics: {goal_analysis.get('primary_metric', 'unknown')}
Data Needed: {goal_analysis.get('data_needed', [])}

Current data sources: {state.get('data_analysis', {}).get('available_sources', [])}

Assess what data we have and what we need to proceed.""")
        ]
        
        response = self.llm.invoke(messages)
        
        data_analysis = self._parse_data_analysis(response.content)
        
        # Determine next agent based on data readiness
        if data_analysis.get("ready_for_modeling"):
            next_agent = "data_scientist"
        elif data_analysis.get("missing_data"):
            next_agent = "data_analyst"  # Stay here until data is available
        else:
            next_agent = "business_consultant"
        
        return {
            "messages": [AIMessage(content=response.content, name=self.name)],
            "current_agent": self.name,
            "data_analysis": data_analysis,
            "next_agent": next_agent
        }
    
    def _parse_data_analysis(self, content: str) -> Dict[str, Any]:
        """Extract structured data analysis."""
        return {
            "analysis": content,
            "ready_for_modeling": "ready" in content.lower() or "sufficient" in content.lower(),
            "missing_data": "missing" in content.lower() or "need" in content.lower()
        }
    
    def _fallback_data_analysis(self, state: AgentState) -> Dict[str, Any]:
        """Fallback data analysis."""
        return {
            "messages": [AIMessage(content="Data analysis requires historical data. [SHOW_UPLOADER: csv]", name=self.name)],
            "data_analysis": {"missing_data": True, "ready_for_modeling": False},
            "next_agent": "data_analyst"
        }


class DataScientistAgent(Agent):
    """Builds models, forecasts, and optimization solutions."""
    
    def __init__(self):
        super().__init__(
            name="data_scientist",
            role="Data Scientist",
            capabilities=[
                "Forecasting models",
                "Optimization algorithms",
                "Statistical analysis",
                "Machine learning",
                "Model validation"
            ],
            system_prompt="""You are a Data Scientist agent specializing in business analytics and optimization.

Your responsibilities:
1. Select appropriate modeling techniques for the business problem
2. Build forecasting models (time series, regression, ML)
3. Create optimization models (linear programming, constraint satisfaction)
4. Validate models and assess accuracy
5. Generate actionable insights from model results

When building solutions:
- Choose simple interpretable models when possible
- Validate with train/test splits or cross-validation
- Report accuracy metrics (MAPE, R², RMSE, etc.)
- Explain model assumptions and limitations
- Provide confidence intervals for predictions

Output format:
- model_type: Type of model used
- accuracy_metrics: Performance statistics
- predictions: Forecast results or optimized solutions
- confidence: Confidence level in results
- assumptions: Key model assumptions
- limitations: Known limitations or caveats
- insights: Business insights from analysis
- next_steps: Recommendations for business consultant"""
        )
    
    def invoke(self, state: AgentState) -> Dict[str, Any]:
        """Build models and generate insights."""
        if not self.llm:
            return self._fallback_modeling(state)
        
        goal = state.get("goal_analysis", {}).get("refined_goal", state["user_goal"])
        data_info = state.get("data_analysis", {})
        
        messages = state["messages"] + [
            SystemMessage(content=self.system_prompt),
            HumanMessage(content=f"""Build a solution for this business problem:

Goal: {goal}
Data Available: {data_info.get('available_data', 'Limited')}
Data Quality: {data_info.get('data_quality', 'Unknown')}

Create appropriate models/analysis and provide insights.""")
        ]
        
        response = self.llm.invoke(messages)
        
        model_results = self._parse_model_results(response.content)
        
        return {
            "messages": [AIMessage(content=response.content, name=self.name)],
            "current_agent": self.name,
            "model_results": model_results,
            "next_agent": "business_consultant"
        }
    
    def _parse_model_results(self, content: str) -> Dict[str, Any]:
        """Extract model results."""
        return {
            "analysis": content,
            "has_results": True
        }
    
    def _fallback_modeling(self, state: AgentState) -> Dict[str, Any]:
        """Fallback modeling."""
        return {
            "messages": [AIMessage(content="Models require more data for accurate predictions.", name=self.name)],
            "model_results": {"has_results": False},
            "next_agent": "business_consultant"
        }


class BusinessConsultantAgent(Agent):
    """Provides strategic recommendations and action plans."""
    
    def __init__(self):
        super().__init__(
            name="business_consultant",
            role="Business Consultant",
            capabilities=[
                "Strategic planning",
                "Action plan creation",
                "Risk assessment",
                "ROI analysis",
                "Change management"
            ],
            system_prompt="""You are a Business Consultant agent specializing in strategic business planning.

Your responsibilities:
1. Synthesize analysis from all other agents
2. Create actionable strategic recommendations
3. Develop phased implementation plans
4. Assess risks and mitigation strategies
5. Estimate ROI and business impact

When creating recommendations:
- Prioritize quick wins and high-impact actions
- Consider resource constraints and budget
- Provide specific, concrete action steps
- Include timelines and milestones
- Identify dependencies and risks

Output a comprehensive business plan with:
- executive_summary: 2-3 sentence overview
- key_recommendations: Top 3-5 strategic actions
- implementation_plan: Phased roadmap with stages
- quick_wins: Immediate actions with high impact
- estimated_timeline: Overall timeframe
- estimated_roi: Expected return on investment
- risks: Key risks and mitigation strategies
- success_metrics: KPIs to track progress"""
        )
    
    def invoke(self, state: AgentState) -> Dict[str, Any]:
        """Generate strategic recommendations."""
        if not self.llm:
            return self._fallback_recommendations(state)
        
        # Gather all previous analysis
        goal_analysis = state.get("goal_analysis", {})
        data_analysis = state.get("data_analysis", {})
        model_results = state.get("model_results", {})
        
        context = f"""Based on comprehensive analysis:

GOAL ANALYSIS:
{json.dumps(goal_analysis, indent=2)}

DATA ANALYSIS:
{json.dumps(data_analysis, indent=2)}

MODEL RESULTS:
{json.dumps(model_results, indent=2)}

Create a strategic business plan with specific recommendations."""
        
        messages = state["messages"] + [
            SystemMessage(content=self.system_prompt),
            HumanMessage(content=context)
        ]
        
        response = self.llm.invoke(messages)
        
        recommendations = self._parse_recommendations(response.content)
        
        return {
            "messages": [AIMessage(content=response.content, name=self.name)],
            "current_agent": self.name,
            "recommendations": recommendations,
            "next_agent": None,  # Terminal agent
            "final_response": response.content
        }
    
    def _parse_recommendations(self, content: str) -> Dict[str, Any]:
        """Extract recommendations."""
        return {
            "plan": content,
            "completed": True
        }
    
    def _fallback_recommendations(self, state: AgentState) -> Dict[str, Any]:
        """Fallback recommendations."""
        goal = state["user_goal"]
        response = f"""Strategic Plan for: {goal}

1. **Goal Clarification**: Define specific, measurable targets
2. **Data Collection**: Gather relevant historical data
3. **Analysis**: Perform detailed data analysis
4. **Implementation**: Execute recommendations in phases
5. **Monitoring**: Track KPIs and adjust as needed

Next steps: Provide more specific details about your goal and available data."""
        
        return {
            "messages": [AIMessage(content=response, name=self.name)],
            "recommendations": {"plan": response},
            "final_response": response,
            "next_agent": None
        }


class OrchestratorAgent:
    """Orchestrates the multi-agent workflow and manages handoffs."""
    
    def __init__(self):
        self.agents = {
            "goal_analyzer": GoalAnalyzerAgent(),
            "data_analyst": DataAnalystAgent(),
            "data_scientist": DataScientistAgent(),
            "business_consultant": BusinessConsultantAgent()
        }
        self.graph = None
        self.llm = None
    
    def configure_llm(self, provider: str = "azure", **kwargs):
        """Configure LLM for all agents."""
        if not LANGGRAPH_AVAILABLE:
            logger.warning("LangGraph not available, using fallback mode")
            return
        
        if provider == "azure":
            self.llm = AzureChatOpenAI(
                azure_endpoint=kwargs.get("azure_endpoint"),
                api_key=kwargs.get("api_key"),
                deployment_name=kwargs.get("deployment_name"),
                api_version=kwargs.get("api_version", "2024-02-15-preview"),
                temperature=kwargs.get("temperature", 0.2)
            )
        else:
            self.llm = ChatOpenAI(
                api_key=kwargs.get("api_key"),
                model=kwargs.get("model", "gpt-4o-mini"),
                temperature=kwargs.get("temperature", 0.2)
            )
        
        # Configure LLM for each agent
        for agent in self.agents.values():
            agent.llm = self.llm
    
    def build_graph(self):
        """Build the LangGraph state machine."""
        if not LANGGRAPH_AVAILABLE:
            logger.warning("LangGraph not available")
            return None
        
        workflow = StateGraph(AgentState)
        
        # Add agent nodes
        for name, agent in self.agents.items():
            workflow.add_node(name, agent.invoke)
        
        # Add router node to determine next agent
        def router(state: AgentState) -> str:
            """Route to next agent based on state."""
            next_agent = state.get("next_agent")
            
            # Check iteration limit
            if state.get("iteration_count", 0) >= state.get("max_iterations", 10):
                return END
            
            if not next_agent:
                return END
            
            return next_agent
        
        # Define edges
        workflow.add_conditional_edges(
            "goal_analyzer",
            router,
            {
                "data_analyst": "data_analyst",
                "business_consultant": "business_consultant",
                END: END
            }
        )
        
        workflow.add_conditional_edges(
            "data_analyst",
            router,
            {
                "data_analyst": "data_analyst",  # Can loop if waiting for data
                "data_scientist": "data_scientist",
                "business_consultant": "business_consultant",
                END: END
            }
        )
        
        workflow.add_conditional_edges(
            "data_scientist",
            router,
            {
                "business_consultant": "business_consultant",
                END: END
            }
        )
        
        workflow.add_conditional_edges(
            "business_consultant",
            router,
            {END: END}
        )
        
        # Set entry point
        workflow.set_entry_point("goal_analyzer")
        
        self.graph = workflow.compile()
        return self.graph
    
    async def process_goal(self, user_goal: str, context: Dict[str, Any] = None, tenant_id: str = None) -> Dict[str, Any]:
        """Process a user goal through the multi-agent system."""
        context = context or {}
        
        # Get available connectors for tenant
        available_connectors = []
        if MCP_TOOLS_AVAILABLE and tenant_id:
            available_connectors = get_tenant_connectors(tenant_id)
        
        initial_state: AgentState = {
            "messages": [HumanMessage(content=user_goal)],
            "user_goal": user_goal,
            "current_agent": "orchestrator",
            "tenant_id": tenant_id,
            "available_connectors": available_connectors,
            "goal_analysis": None,
            "data_analysis": context.get("data_analysis"),
            "model_results": None,
            "recommendations": None,
            "next_agent": "goal_analyzer",
            "final_response": None,
            "iteration_count": 0,
            "max_iterations": 10
        }
        
        if not LANGGRAPH_AVAILABLE or not self.graph:
            logger.info("Using fallback mode without LangGraph")
            return await self._fallback_process(user_goal, context)
        
        # Run the graph
        final_state = await self.graph.ainvoke(initial_state)
        
        return {
            "response": final_state.get("final_response", "Analysis complete"),
            "goal_analysis": final_state.get("goal_analysis"),
            "data_analysis": final_state.get("data_analysis"),
            "model_results": final_state.get("model_results"),
            "recommendations": final_state.get("recommendations"),
            "conversation": [m.content for m in final_state.get("messages", [])]
        }
    
    async def _fallback_process(self, user_goal: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback processing without LangGraph."""
        # Sequential agent execution
        state = {
            "messages": [],
            "user_goal": user_goal,
            "current_agent": "",
            "goal_analysis": None,
            "data_analysis": context.get("data_analysis"),
            "model_results": None,
            "recommendations": None,
            "next_agent": None,
            "final_response": None,
            "iteration_count": 0,
            "max_iterations": 5
        }
        
        # Goal analysis
        state.update(self.agents["goal_analyzer"].invoke(state))
        
        # Data analysis
        if state.get("data_analysis") or state.get("next_agent") == "data_analyst":
            state.update(self.agents["data_analyst"].invoke(state))
        
        # Data science (if data is ready)
        if state.get("data_analysis", {}).get("ready_for_modeling"):
            state.update(self.agents["data_scientist"].invoke(state))
        
        # Business recommendations
        state.update(self.agents["business_consultant"].invoke(state))
        
        return {
            "response": state.get("final_response", "Analysis complete"),
            "goal_analysis": state.get("goal_analysis"),
            "data_analysis": state.get("data_analysis"),
            "model_results": state.get("model_results"),
            "recommendations": state.get("recommendations"),
            "conversation": [m.content for m in state.get("messages", []) if hasattr(m, 'content')]
        }
