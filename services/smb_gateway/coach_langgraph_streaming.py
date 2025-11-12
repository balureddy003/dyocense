"""
LangGraph Streaming Adapter

Converts LangGraph .stream() events into SSE format compatible with frontend
"""
import json
import logging
from typing import Any, AsyncGenerator, Dict, List

logger = logging.getLogger(__name__)


async def stream_langgraph_to_sse(
    workflow,
    initial_state: Dict[str, Any],
    config: Dict[str, Any]
) -> AsyncGenerator[str, None]:
    """
    Stream LangGraph execution as Server-Sent Events
    
    Yields SSE-formatted chunks that match the frontend's expected format
    """
    
    current_task_index = 0
    sub_tasks = []
    
    try:
        # Stream workflow execution
        async for event in workflow.astream(initial_state, config, stream_mode="updates"):
            # Event structure: {node_name: state_update}
            for node_name, state_update in event.items():
                logger.debug(f"[LangGraph Stream] Node: {node_name}")
                
                # Handle different node types
                if node_name == "analyze_intent":
                    # Intent analysis completed, got sub_tasks
                    sub_tasks = state_update.get('sub_tasks', [])
                    intent = state_update.get('intent', 'unknown')
                    
                    yield format_sse_chunk(
                        delta=f"🎯 Intent detected: {intent}\n",
                        done=False,
                        metadata={
                            'phase': 'planning',
                            'intent': intent,
                            'total_tasks': len(sub_tasks)
                        }
                    )
                
                elif node_name == "execute_task":
                    # Task execution update
                    task_idx = state_update.get('current_task_index', 0) - 1
                    if task_idx >= 0 and task_idx < len(sub_tasks):
                        task = sub_tasks[task_idx]
                        task_id = task.get('id')
                        description = task.get('description', '')
                        status = task.get('status', 'pending')
                        
                        # Send task description
                        yield format_sse_chunk(
                            delta=f"{description}\n",
                            done=False,
                            metadata={
                                'phase': 'task_execution',
                                'task_id': task_id,
                                'task_status': status
                            }
                        )
                        
                        # Send completion marker
                        if status == 'completed':
                            yield format_sse_chunk(
                                delta='✓ ',
                                done=False,
                                metadata={
                                    'phase': 'task_execution',
                                    'task_id': task_id,
                                    'task_status': 'completed'
                                }
                            )
                        elif status == 'failed':
                            yield format_sse_chunk(
                                delta='✗ Failed\n',
                                done=False,
                                metadata={
                                    'phase': 'task_execution',
                                    'task_id': task_id,
                                    'task_status': 'failed'
                                }
                            )
                
                elif node_name == "check_approval":
                    # Human-in-the-loop gate reached
                    pending = state_update.get('pending_approval')
                    if pending:
                        task_id = pending.get('task_id')
                        proposed_result = pending.get('proposed_result')
                        
                        yield format_sse_chunk(
                            delta='⏸ Awaiting your approval\n',
                            done=False,
                            metadata={
                                'phase': 'task_execution',
                                'task_id': task_id,
                                'task_status': 'awaiting_human',
                                'review_id': task_id,  # Use task_id as review_id
                                'proposed_result': proposed_result
                            }
                        )
                        
                        # End stream for human review
                        yield format_sse_chunk(
                            delta='',
                            done=True,
                            metadata={
                                'phase': 'task_execution',
                                'task_id': task_id,
                                'task_status': 'awaiting_human'
                            }
                        )
                        return
                
                elif node_name == "generate_report":
                    # Report generated - just set metadata, don't clutter the chat
                    report_id = state_update.get('report_id')
                    if report_id:
                        # Only send metadata, the UI will show download buttons separately
                        yield format_sse_chunk(
                            delta='',
                            done=False,
                            metadata={
                                'phase': 'report_generated',
                                'report_id': report_id
                            }
                        )
                
                elif node_name == "generate_analysis":
                    # Final AI analysis - no announcement needed, just stream the content
                    pass
                    
                    final_response = state_update.get('final_response', '')
                    if final_response:
                        # Stream response in chunks for smooth display
                        chunk_size = 50
                        for i in range(0, len(final_response), chunk_size):
                            chunk = final_response[i:i+chunk_size]
                            yield format_sse_chunk(
                                delta=chunk,
                                done=False,
                                metadata={'phase': 'analysis'}
                            )
        
        # Stream complete
        yield format_sse_chunk(
            delta='',
            done=True,
            metadata={'phase': 'complete'}
        )
    
    except Exception as e:
        logger.error(f"[LangGraph Stream] Error: {e}", exc_info=True)
        yield format_sse_chunk(
            delta=f"\n\nError during analysis: {str(e)}",
            done=True,
            metadata={'error': str(e)}
        )


def format_sse_chunk(delta: str, done: bool, metadata: Dict[str, Any]) -> str:
    """Format a chunk as Server-Sent Event"""
    chunk = {
        "delta": delta,
        "done": done,
        "metadata": metadata
    }
    return f"data: {json.dumps(chunk)}\n\n"
