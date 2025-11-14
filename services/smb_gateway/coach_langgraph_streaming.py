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
    
    Yields SSE-formatted chunks that match the frontend's expected format.
    Enhanced to provide engaging, real-time insights during analysis.
    """
    
    current_task_index = 0
    sub_tasks = []
    business_name = initial_state.get('business_context', {}).get('business_name', 'your business')
    
    try:
        # Stream workflow execution
        async for event in workflow.astream(initial_state, config, stream_mode="updates"):
            # Event structure: {node_name: state_update}
            for node_name, state_update in event.items():
                logger.debug(f"[LangGraph Stream] Node: {node_name}")
                
                # Handle different node types with engaging messages
                if node_name == "analyze_intent":
                    # Intent analysis completed, got sub_tasks
                    sub_tasks = state_update.get('sub_tasks', [])
                    intent = state_update.get('intent', 'unknown')
                    
                    # Send engaging intro based on intent
                    intent_messages = {
                        'inventory_analysis': f"Let me analyze your inventory for {business_name}. I'll examine stock levels, product performance, and identify optimization opportunities...\n\n",
                        'revenue_analysis': f"I'm diving into your revenue data for {business_name}. Looking at sales trends, top performers, and growth opportunities...\n\n",
                        'general_analysis': f"I'm analyzing the overall health of {business_name}. Let me examine key metrics and identify actionable insights...\n\n"
                    }
                    
                    intro_message = intent_messages.get(intent, f"Starting analysis for {business_name}...\n\n")
                    
                    yield format_sse_chunk(
                        delta=intro_message,
                        done=False,
                        metadata={
                            'phase': 'planning',
                            'intent': intent,
                            'total_tasks': len(sub_tasks)
                        }
                    )
                
                elif node_name == "execute_task":
                    # Task execution update with conversational progress
                    task_idx = state_update.get('current_task_index', 0) - 1
                    if task_idx >= 0 and task_idx < len(sub_tasks):
                        task = sub_tasks[task_idx]
                        task_id = task.get('id')
                        description = task.get('description', '')
                        status = task.get('status', 'pending')
                        
                        # Get task results for intermediate insights
                        task_results = state_update.get('task_results', {})
                        task_result = task_results.get(task_id)
                        
                        # Send engaging task start message
                        task_intros = {
                            'discover_schema': "📊 First, let me understand your data structure...\n",
                            'analyze_inventory_volume': "📦 Checking inventory levels across your products...\n",
                            'analyze_inventory_value': "💰 Calculating total inventory value and stock worth...\n",
                            'identify_top_products': "⭐ Identifying your best-performing products...\n",
                            'detect_stock_issues': "⚠️ Scanning for potential stock issues...\n",
                            'calculate_revenue': "💵 Analyzing revenue streams and patterns...\n",
                            'analyze_order_trends': "📈 Examining order trends over time...\n"
                        }
                        
                        if status == 'pending' and task_id in task_intros:
                            yield format_sse_chunk(
                                delta=task_intros[task_id],
                                done=False,
                                metadata={
                                    'phase': 'task_execution',
                                    'task_id': task_id,
                                    'task_status': 'running'
                                }
                            )
                        
                        # Stream intermediate insights when task completes
                        if status == 'completed' and task_result:
                            insight = _format_task_insight(task_id, task_result)
                            if insight:
                                yield format_sse_chunk(
                                    delta=insight,
                                    done=False,
                                    metadata={
                                        'phase': 'task_execution',
                                        'task_id': task_id,
                                        'task_status': 'completed',
                                        'has_insight': True
                                    }
                                )
                        elif status == 'failed':
                            yield format_sse_chunk(
                                delta=f"⚠️ Couldn't complete {description}, but continuing with other analysis...\n\n",
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
                            delta='\n\n⏸ **Quick Check:** I found something that needs your input before proceeding...\n',
                            done=False,
                            metadata={
                                'phase': 'task_execution',
                                'task_id': task_id,
                                'task_status': 'awaiting_human',
                                'review_id': task_id,
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
                    # Report generated - announce it conversationally
                    report_id = state_update.get('report_id')
                    if report_id:
                        yield format_sse_chunk(
                            delta="\n\n📄 I've prepared a detailed report with all the data and charts. You can download it from the sidebar.\n\n",
                            done=False,
                            metadata={
                                'phase': 'report_generated',
                                'report_id': report_id
                            }
                        )
                
                elif node_name == "generate_analysis":
                    # Signal start of final analysis
                    yield format_sse_chunk(
                        delta="Now let me pull this all together into actionable recommendations...\n\n---\n\n",
                        done=False,
                        metadata={'phase': 'analysis', 'analysis_starting': True}
                    )
                    
                    final_response = state_update.get('final_response', '')
                    if final_response:
                        # Stream response in smaller chunks for smooth typing effect
                        chunk_size = 30
                        for i in range(0, len(final_response), chunk_size):
                            chunk = final_response[i:i+chunk_size]
                            yield format_sse_chunk(
                                delta=chunk,
                                done=False,
                                metadata={'phase': 'analysis'}
                            )
                
                elif node_name == "generate_visual_response":
                    # Multi-agent visualization system completed
                    visual_response = state_update.get('visual_response', {})
                    if visual_response:
                        logger.info(f"[LangGraph Stream] Sending visual response: {len(visual_response.get('charts', []))} charts, "
                                   f"{len(visual_response.get('actions', []))} actions")
                        
                        # Send visual components as structured metadata
                        yield format_sse_chunk(
                            delta="",  # No text delta
                            done=False,
                            metadata={
                                'phase': 'visualization',
                                'visual_response': visual_response  # Send entire structured UI spec
                            }
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
            delta=f"\n\n⚠️ Encountered an issue during analysis: {str(e)}\n\nLet me try to provide what insights I can...\n\n",
            done=True,
            metadata={'error': str(e)}
        )


def _format_task_insight(task_id: str, task_result: Any) -> str:
    """
    Format intermediate insights from completed tasks.
    Makes the conversation engaging by sharing discoveries as they happen.
    """
    if not task_result or not isinstance(task_result, dict):
        return ""
    
    # Format insights based on task type
    if task_id == 'discover_schema':
        record_count = task_result.get('total_records', 0)
        data_types = task_result.get('available_data', [])
        if record_count > 0:
            return f"✓ Found {record_count:,} records across {len(data_types)} data sources.\n\n"
    
    elif task_id == 'analyze_inventory_volume':
        total_items = task_result.get('total_items', 0)
        low_stock = task_result.get('low_stock_count', 0)
        if total_items > 0:
            insight = f"✓ You have {total_items} products in inventory"
            if low_stock > 0:
                insight += f", with {low_stock} items running low"
            return insight + ".\n\n"
    
    elif task_id == 'analyze_inventory_value':
        total_value = task_result.get('total_value', 0)
        if total_value > 0:
            return f"✓ Total inventory value: ${total_value:,.2f}\n\n"
    
    elif task_id == 'identify_top_products':
        top_products = task_result.get('top_products', [])
        if top_products:
            product_names = [p.get('name', 'Unknown') for p in top_products[:3]]
            return f"✓ Top performers: {', '.join(product_names)}\n\n"
    
    elif task_id == 'detect_stock_issues':
        issues = task_result.get('issues', [])
        if issues:
            return f"⚠️ Found {len(issues)} items needing attention.\n\n"
        else:
            return f"✓ No critical stock issues detected!\n\n"
    
    elif task_id == 'calculate_revenue':
        revenue = task_result.get('total_revenue', 0)
        growth = task_result.get('growth_rate', 0)
        if revenue > 0:
            insight = f"✓ Revenue: ${revenue:,.2f}"
            if growth != 0:
                trend = "up" if growth > 0 else "down"
                insight += f" (trending {trend} {abs(growth):.1f}%)"
            return insight + "\n\n"
    
    elif task_id == 'analyze_order_trends':
        trend = task_result.get('trend', 'stable')
        avg_orders = task_result.get('avg_daily_orders', 0)
        if avg_orders > 0:
            return f"✓ Orders averaging {avg_orders:.0f}/day, trend is {trend}.\n\n"
    
    # Generic fallback
    if 'summary' in task_result:
        return f"✓ {task_result['summary']}\n\n"
    
    return "✓ Completed\n\n"


def format_sse_chunk(delta: str, done: bool, metadata: Dict[str, Any]) -> str:
    """Format a chunk as Server-Sent Event"""
    chunk = {
        "delta": delta,
        "done": done,
        "metadata": metadata
    }
    return f"data: {json.dumps(chunk)}\n\n"
