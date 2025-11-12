"""
LangGraph Human-in-the-Loop Resume Handler

Uses LangGraph's update_state() to resume after human approval
"""
import logging
from typing import Any, Dict

from .coach_langgraph_workflow import get_coach_workflow

logger = logging.getLogger(__name__)


async def resume_langgraph_execution(
    thread_id: str,
    approved: bool,
    feedback: str | None = None,
    corrections: Dict[str, Any] | None = None
):
    """
    Resume a paused LangGraph workflow after human review
    
    Args:
        thread_id: The conversation thread ID
        approved: Whether the human approved the step
        feedback: Optional human feedback
        corrections: Optional corrections to apply to the result
    
    Returns:
        Updated workflow ready to continue streaming
    """
    workflow = get_coach_workflow()
    
    # Get current state
    state = workflow.get_state({"configurable": {"thread_id": thread_id}})
    
    if not state or not state.values.get('pending_approval'):
        raise ValueError(f"No pending approval found for thread {thread_id}")
    
    # Build human feedback to inject into state
    human_feedback_str = f"{'Approved' if approved else 'Rejected'}"
    if feedback:
        human_feedback_str += f": {feedback}"
    
    # Update state to clear pending approval and add human feedback
    state_update = {
        "human_feedback": human_feedback_str,
        "pending_approval": None  # Clear the approval gate
    }
    
    # If approved and corrections provided, merge them into task results
    if approved and corrections:
        pending = state.values.get('pending_approval', {})
        task_id = pending.get('task_id')
        if task_id:
            task_results = state.values.get('task_results', {})
            # Merge corrections
            if task_id in task_results and isinstance(task_results[task_id], dict):
                task_results[task_id] = {**task_results[task_id], **corrections}
            else:
                task_results[task_id] = corrections
            state_update['task_results'] = task_results
    
    # Update state in checkpoint
    workflow.update_state(
        {"configurable": {"thread_id": thread_id}},
        state_update,
        as_node="check_approval"  # Resume from the approval check node
    )
    
    logger.info(f"[LangGraph Resume] Updated state for thread {thread_id}, approved={approved}")
    
    return workflow, {"configurable": {"thread_id": thread_id}}
