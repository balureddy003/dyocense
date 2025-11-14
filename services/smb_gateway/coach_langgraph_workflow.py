"""
LangGraph-based Coach Workflow

Replaces custom task planner with native LangGraph capabilities:
- StateGraph for orchestration
- Built-in human-in-the-loop with interrupts
- Checkpointing for resume
- Native streaming
"""
import json
import logging
import os
from datetime import datetime
from typing import Any, Dict, List, Literal, Optional, TypedDict, Annotated

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage
from pydantic import BaseModel

from packages.llm import _invoke_llm
from services.smb_gateway.coach_multi_agent_viz import generate_visual_response

logger = logging.getLogger(__name__)

# Try PostgresSaver if available
try:
    from langgraph.checkpoint.postgres import PostgresSaver
    POSTGRES_AVAILABLE = True
except ImportError:
    POSTGRES_AVAILABLE = False
    PostgresSaver = None


# ============================================================================
# State Schema
# ============================================================================

class CoachState(TypedDict):
    """LangGraph state for coach workflow"""
    # Input
    tenant_id: str
    user_message: str
    conversation_history: List[BaseMessage]
    
    # Business context
    business_context: Dict[str, Any]
    available_data: Dict[str, List[Dict[str, Any]]]
    
    # Workflow tracking
    intent: Optional[str]
    sub_tasks: List[Dict[str, Any]]
    completed_tasks: List[Dict[str, Any]]
    current_task_index: int
    
    # Results
    task_results: Dict[str, Any]
    report_id: Optional[str]
    final_response: str
    
    # Multi-agent visualization results
    visual_response: Optional[Dict[str, Any]]  # Structured UI components
    
    # Human-in-the-loop
    pending_approval: Optional[Dict[str, Any]]
    human_feedback: Optional[str]


# ============================================================================
# Workflow Nodes
# ============================================================================

def analyze_intent_node(state: CoachState) -> CoachState:
    """Analyze user intent and plan sub-tasks"""
    logger.info(f"[LangGraph] Analyzing intent for: {state['user_message'][:100]}")
    
    query_lower = state['user_message'].lower()
    available_data = state['available_data']
    
    # Build task plan based on intent
    sub_tasks = []
    intent = "general_query"
    
    # Always start with schema discovery
    sub_tasks.append({
        "id": "discover_schema",
        "description": "🔍 Discovering data structure",
        "status": "pending"
    })
    
    # Intent-based task planning
    if any(word in query_lower for word in ["inventory", "stock", "product"]):
        intent = "inventory_analysis"
        sub_tasks.extend([
            {"id": "analyze_inventory_volume", "description": "📦 Analyzing inventory volume", "status": "pending"},
            {"id": "analyze_inventory_value", "description": "💰 Calculating inventory value", "status": "pending"},
            {"id": "identify_top_products", "description": "⭐ Identifying top products", "status": "pending"},
            {"id": "detect_stock_issues", "description": "⚠️ Detecting stock issues", "status": "pending"}
        ])
    elif any(word in query_lower for word in ["revenue", "sales", "order"]):
        intent = "revenue_analysis"
        sub_tasks.extend([
            {"id": "calculate_revenue", "description": "💵 Calculating revenue metrics", "status": "pending"},
            {"id": "analyze_order_trends", "description": "📈 Analyzing order trends", "status": "pending"}
        ])
    else:
        intent = "general_analysis"
        sub_tasks.extend([
            {"id": "generate_overview", "description": "📊 Generating business overview", "status": "pending"}
        ])
    
    # Optionally add report generation
    # Only require approval for complex reports or if explicitly requested
    requires_report_approval = any(word in query_lower for word in ["report", "detailed analysis", "comprehensive"])
    
    sub_tasks.append({
        "id": "generate_report",
        "description": "📝 Generating detailed report",
        "status": "pending",
        "requires_approval": requires_report_approval
    })
    
    state['intent'] = intent
    state['sub_tasks'] = sub_tasks
    state['current_task_index'] = 0
    state['completed_tasks'] = []
    state['task_results'] = {}
    
    logger.info(f"[LangGraph] Intent: {intent}, Tasks: {len(sub_tasks)}")
    return state


def execute_task_node(state: CoachState) -> CoachState:
    """Execute current task"""
    current_idx = state['current_task_index']
    sub_tasks = state['sub_tasks']
    
    if current_idx >= len(sub_tasks):
        logger.info("[LangGraph] All tasks completed")
        return state
    
    task = sub_tasks[current_idx]
    task_id = task['id']
    logger.info(f"[LangGraph] Executing task: {task_id}")
    
    # Import task handlers
    from .task_planner import get_task_planner
    planner = get_task_planner()
    
    # Get handler for this task
    handler = planner._task_handlers.get(task_id)
    
    if handler:
        try:
            result = handler(state['available_data'])
            task['status'] = 'completed'
            task['result'] = result
            state['task_results'][task_id] = result
            state['completed_tasks'].append(task)
            logger.info(f"[LangGraph] ✓ Task {task_id} completed")
        except Exception as e:
            task['status'] = 'failed'
            task['error'] = str(e)
            logger.error(f"[LangGraph] ✗ Task {task_id} failed: {e}")
    else:
        task['status'] = 'not_implemented'
        logger.warning(f"[LangGraph] Task {task_id} has no handler")
    
    state['current_task_index'] += 1
    return state


def check_approval_needed_node(state: CoachState) -> CoachState:
    """Check if current task needs human approval"""
    current_idx = state['current_task_index'] - 1  # Just completed
    if current_idx < 0 or current_idx >= len(state['sub_tasks']):
        return state
    
    task = state['sub_tasks'][current_idx]
    
    if task.get('requires_approval'):
        logger.info(f"[LangGraph] ⏸ Task {task['id']} requires human approval")
        state['pending_approval'] = {
            'task_id': task['id'],
            'task_description': task['description'],
            'proposed_result': task.get('result'),
        }
    
    return state


def apply_human_feedback_node(state: CoachState) -> CoachState:
    """Apply human feedback/corrections after approval"""
    approval = state.get('pending_approval')
    if not approval:
        return state
    
    logger.info("[LangGraph] Applying human feedback")
    
    task_id = approval['task_id']
    
    # If human provided corrections, merge them
    if state.get('human_feedback'):
        # In a real scenario, parse and apply corrections
        logger.info(f"[LangGraph] Human feedback received: {state['human_feedback']}")
    
    # Clear pending approval
    state['pending_approval'] = None
    
    return state


def generate_report_node(state: CoachState) -> CoachState:
    """Generate downloadable report from task results"""
    logger.info("[LangGraph] Generating report")
    
    from .report_generator import get_report_generator, BusinessReport, ReportSection, AgentThought, Evidence
    
    report_generator = get_report_generator()
    business_name = state['business_context'].get('business_name', 'Business')
    
    report = BusinessReport(
        title="Business Analysis Report",
        business_name=business_name,
        report_type="comprehensive_analysis"
    )
    
    # Build sections from completed tasks
    for task in state['completed_tasks']:
        if task.get('status') == 'completed' and task.get('result'):
            result = task['result']
            
            # Extract agent thoughts
            agent_thoughts = []
            if "agent_thoughts" in result:
                for thought_data in result["agent_thoughts"]:
                    agent_thoughts.append(AgentThought(
                        agent_name=thought_data.get("agent", "Analysis Agent"),
                        thought=thought_data.get("thought", ""),
                        action=thought_data.get("action", ""),
                        observation=thought_data.get("observation", ""),
                        data_source=thought_data.get("data_source", "")
                    ))
            
            # Extract evidence
            evidence_list = []
            if "evidence" in result:
                for ev_data in result["evidence"]:
                    evidence_list.append(Evidence(
                        claim=ev_data.get("claim", ""),
                        data_source=ev_data.get("data_source", ""),
                        calculation=ev_data.get("calculation", ""),
                        raw_value=ev_data.get("value", ""),
                        confidence=ev_data.get("confidence", 1.0)
                    ))
            
            section = ReportSection(
                title=task['description'],
                content=f"Analysis completed for: {task['description']}",
                data=result,
                insights=[],
                recommendations=[],
                agent_thoughts=agent_thoughts,
                evidence=evidence_list
            )
            report.add_section(section)
    
    report.set_summary(f"Analyzed data for {business_name} across {len(state['completed_tasks'])} dimensions.")
    
    state['report_id'] = report.report_id
    logger.info(f"[LangGraph] Report generated: {report.report_id}")
    
    # Store report (you'll need to pass tenant_id through state)
    # For now, just return the ID
    return state


def generate_analysis_node(state: CoachState) -> CoachState:
    """Generate final AI analysis using LLM with rich formatting and action plans"""
    logger.info("[LangGraph] Generating AI analysis")
    
    # Build context for LLM
    business_context = state['business_context']
    task_results = state['task_results']
    user_message = state['user_message']
    
    # Extract health context
    health_score_data = business_context.get('health_score', {})
    if isinstance(health_score_data, dict):
        health_score = health_score_data.get('score', 'N/A')
        health_trend = health_score_data.get('trend', 'N/A')
        breakdown = health_score_data.get('breakdown', {})
    else:
        health_score = health_score_data
        health_trend = 'N/A'
        breakdown = {}
    
    # Extract alerts and signals with details
    alerts = business_context.get('alerts', [])
    signals = business_context.get('signals', [])
    goals = business_context.get('goals', [])
    tasks = business_context.get('tasks', [])
    
    # Build alert summary
    alert_summary = ""
    if alerts:
        alert_titles = [a.get('title', 'Unknown') for a in alerts[:3]]
        alert_summary = f"Critical issues: {', '.join(alert_titles)}"
    
    # Build signal summary
    signal_summary = ""
    if signals:
        signal_titles = [s.get('title', 'Unknown') for s in signals[:3]]
        signal_summary = f"Positive trends: {', '.join(signal_titles)}"
    
    # Build comprehensive analysis prompt with conversational style
    prompt = f"""You are a senior business analyst conducting a live review with the owner of {business_context.get('business_name', 'this business')}. You've just finished analyzing their data and are now presenting your findings in a conversational, engaging way.

**THEIR QUESTION:**
"{user_message}"

**BUSINESS HEALTH SNAPSHOT:**
- Overall Health Score: {health_score}/100 (trending {health_trend})
- Revenue Health: {breakdown.get('revenue', 'N/A')}/100
- Operations Health: {breakdown.get('operations', 'N/A')}/100
- Customer Health: {breakdown.get('customer', 'N/A')}/100
- {alert_summary if alert_summary else "No critical alerts"}
- {signal_summary if signal_summary else "Limited positive signals"}
- Active Goals: {len(goals)}
- Pending Tasks: {len(tasks)}

**DETAILED DATA FROM YOUR ANALYSIS:**
{json.dumps(task_results, indent=2, default=str)}

**YOUR ROLE:**
You're having a conversation with a busy business owner who needs ACTIONABLE insights, not generic advice. Reference SPECIFIC numbers from the data, explain the "why" behind your recommendations, and make them feel like you understand their unique situation.

**RESPONSE GUIDELINES:**

1. **Start Conversationally** (2-3 paragraphs):
   - Open with what immediately stands out from their data
   - Reference specific numbers (e.g., "I see you have 47 overdue invoices worth $12,500...")
   - Connect to their health score and explain what it means
   - Show you understand their question and situation

2. **Prioritized Action Plan** (4-6 specific actions):
   - **Be specific with numbers**: Instead of "follow up on invoices", say "Contact the 3 clients with invoices over $5,000 overdue"
   - **Explain urgency**: Use phrases like "This is critical because..." or "I'm prioritizing this because..."
   - **Reference their data**: Connect each action to something you found in the analysis
   - **Make it practical**: Actions they can complete in 7 days, not vague strategies
   
   Format as:
   ## 🎯 Your Action Plan for the Next 7 Days
   
   **This Week's Top Priority:**
   [The ONE thing that will make the biggest impact, with specific numbers and deadline]
   
   **Day 1-2: Immediate Actions**
   - **[Specific action with numbers]** - [Why this matters based on your data]
   
   **Day 3-5: Follow-Through**
   - **[Next steps based on data]** - [Expected outcome with metrics]
   
   **Day 6-7: Optimization**
   - **[Longer-term improvement]** - [How this prevents future issues]

3. **Data-Backed Insights** (3-4 findings):
   - Each insight MUST reference actual numbers from task_results
   - Explain what the numbers mean in plain English
   - Connect to revenue, cash flow, or customer impact
   
   Format as:
   ## 💡 What the Data Shows
   
   **[Insight based on actual data]**
   Looking at your [specific data source], I found [specific number/pattern]. This means [business impact]. I recommend [specific action].

4. **Quick Wins** (2-3 easy actions):
   Things they can do TODAY that will improve their health score or address alerts.

5. **What to Monitor** (3 specific metrics):
   Based on their data, what numbers should they check daily/weekly?

**TONE & STYLE:**
- Conversational, like you're sitting across from them
- Use "I see..." "I noticed..." "Let me show you..."
- Avoid jargon - explain in plain English
- Show empathy for challenges revealed in the data
- Be encouraging about strengths, honest about issues
- Reference their business name naturally in conversation

**CRITICAL RULES:**
- ALWAYS cite specific numbers from the task_results data
- If you don't have data, say "I don't have visibility into X, but..."
- Connect everything back to their health score of {health_score}/100
- Make every recommendation actionable within 7 days
- End with ONE clear next step they should take TODAY

Generate your response now as if you're presenting live to them:
- Use - for bullet points
- Use numbered lists for sequential actions
- Include emojis for visual guidance (📊 🎯 💡 ⚠️ 📈)
- Be specific with numbers, dates, and metrics
- Keep tone encouraging but honest about challenges
- Make every recommendation actionable and measurable
"""
    
    try:
        response = _invoke_llm(
            prompt=prompt,
            temperature=0.8,  # Increased for more conversational, varied responses
            max_tokens=2500  # Increased for detailed, data-rich response
        )
        state['final_response'] = response if isinstance(response, str) else str(response)
        logger.info(f"[LangGraph] Generated analysis: {len(state['final_response'])} chars")
    except Exception as e:
        logger.error(f"[LangGraph] LLM generation failed: {e}")
        # Fallback with conversational format
        state['final_response'] = f"""I've reviewed your data for {business_context.get('business_name', 'your business')}, and here's what I found:

**Quick Take:** Your health score is at {health_score}/100, which {
    'shows strong performance' if health_score >= 70 else
    'indicates some challenges' if health_score >= 40 else
    'needs immediate attention'
}.

## 🎯 Your Priority Actions This Week

**Right Now:**
- Review your {len(alerts)} critical alerts - these need immediate attention
- Leverage your {len(signals)} positive trends to maintain momentum

**This Week:**
- Focus on your {len(goals)} active goals
- Work through your {len(tasks)} pending tasks

## 💡 What to Watch

Keep an eye on the metrics that feed into your health score, especially in areas scoring below 60.

**Bottom Line:** Start with addressing your highest-priority alert today, then build from there.

*Note: I encountered a system limitation generating the full analysis. Try asking a more specific question for detailed insights.*

## 💡 Key Insight

Your business data has been analyzed. Check the generated report for detailed insights.

**Note:** Full analysis temporarily unavailable due to system limits. Please try asking a more specific question.
"""
    
    return state


def generate_visual_response_node(state: CoachState) -> CoachState:
    """Multi-Agent Visualization System - Generate structured UI components instead of text"""
    logger.info("[LangGraph] Generating visual response with multi-agent system")
    
    try:
        visual_response = generate_visual_response(
            business_context=state['business_context'],
            task_results=state['task_results'],
            user_message=state['user_message']
        )
        state['visual_response'] = visual_response
        logger.info(f"[LangGraph] Visual response generated: {len(visual_response.get('charts', []))} charts, "
                   f"{len(visual_response.get('actions', []))} actions, {len(visual_response.get('kpis', []))} KPIs")
    except Exception as e:
        logger.error(f"[LangGraph] Visual response generation failed: {e}")
        # Fallback to minimal response
        state['visual_response'] = {
            "summary": "Unable to generate visualizations. Please try again.",
            "kpis": [],
            "charts": [],
            "tables": [],
            "actions": [],
            "insights": []
        }
    
    return state


# ============================================================================
# Conditional Edges
# ============================================================================

def should_continue_tasks(state: CoachState) -> Literal["execute_task", "check_approval", "generate_report"]:
    """Decide next step after task execution"""
    current_idx = state['current_task_index']
    
    # Check if just-completed task requires approval
    completed_idx = current_idx - 1
    if 0 <= completed_idx < len(state['sub_tasks']):
        task = state['sub_tasks'][completed_idx]
        if task.get('requires_approval') and task.get('status') == 'completed':
            return "check_approval"
    
    # If more tasks, continue execution
    if current_idx < len(state['sub_tasks']):
        return "execute_task"
    
    # All tasks done, generate report
    return "generate_report"


# ============================================================================
# Build Workflow
# ============================================================================

def build_coach_workflow(checkpointer=None):
    """Build the LangGraph workflow"""
    
    workflow = StateGraph(CoachState)
    
    # Add nodes
    workflow.add_node("analyze_intent", analyze_intent_node)
    workflow.add_node("execute_task", execute_task_node)
    workflow.add_node("check_approval", check_approval_needed_node)
    workflow.add_node("apply_feedback", apply_human_feedback_node)
    workflow.add_node("generate_report", generate_report_node)
    workflow.add_node("generate_analysis", generate_analysis_node)
    workflow.add_node("generate_visual_response", generate_visual_response_node)  # NEW: Multi-agent visualization
    
    # Entry point
    workflow.set_entry_point("analyze_intent")
    
    # Flow
    workflow.add_edge("analyze_intent", "execute_task")
    
    workflow.add_conditional_edges(
        "execute_task",
        should_continue_tasks,
        {
            "execute_task": "execute_task",
            "check_approval": "check_approval",
            "generate_report": "generate_report"
        }
    )
    
    # Human-in-the-loop: check_approval sets pending_approval, then always goes to apply_feedback
    # The interrupt happens before apply_feedback when there's a pending approval
    workflow.add_edge("check_approval", "apply_feedback")
    
    workflow.add_edge("apply_feedback", "execute_task")
    workflow.add_edge("generate_report", "generate_analysis")
    workflow.add_edge("generate_analysis", "generate_visual_response")  # UPDATED: Visual after text
    workflow.add_edge("generate_visual_response", END)  # UPDATED: End after visuals
    
    # Compile with checkpointer
    # interrupt_before=["apply_feedback"] means: pause before apply_feedback if we reach it
    # We only reach apply_feedback via check_approval, which only happens when approval is required
    if checkpointer:
        return workflow.compile(checkpointer=checkpointer, interrupt_before=["apply_feedback"])
    return workflow.compile(interrupt_before=["apply_feedback"])


# ============================================================================
# Convenience Functions
# ============================================================================

def get_checkpointer():
    """Get appropriate checkpointer based on environment"""
    postgres_url = os.getenv("POSTGRES_URL")
    if postgres_url and POSTGRES_AVAILABLE and PostgresSaver:
        try:
            return PostgresSaver.from_conn_string(postgres_url)  # type: ignore
        except Exception as e:
            logger.warning(f"Failed to create PostgresSaver: {e}, falling back to MemorySaver")
    
    return MemorySaver()


_workflow = None

def get_coach_workflow():
    """Get singleton workflow instance"""
    global _workflow
    if _workflow is None:
        checkpointer = get_checkpointer()
        _workflow = build_coach_workflow(checkpointer)
    return _workflow
