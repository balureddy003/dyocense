"""
Multi-Agent Visualization System for Coach

Instead of wall-of-text responses, this system uses specialized agents to create:
- Charts and visualizations
- Data tables with comparisons
- Actionable task cards
- KPI widgets
- Timeline views

Agents:
1. Data Extraction Agent - Pulls key metrics from task_results
2. Visualization Agent - Creates chart specs (type, data, config)
3. Action Agent - Generates actionable task cards
4. Presentation Agent - Orchestrates final structured response
"""
import json
import logging
from typing import Any, Dict, List, Optional

from packages.llm import _invoke_llm

logger = logging.getLogger(__name__)


def generate_visual_response(
    business_context: Dict[str, Any],
    task_results: Dict[str, Any],
    user_message: str
) -> Dict[str, Any]:
    """
    Generate a structured visual response instead of plain text.
    
    Returns a structure like:
    {
        "summary": "Quick 2-sentence takeaway",
        "kpis": [{"label": "Health Score", "value": 45, "trend": "down", "color": "red"}],
        "charts": [{"type": "bar", "title": "...", "data": [...]}],
        "tables": [{"title": "...", "headers": [...], "rows": [...]}],
        "actions": [{"priority": "high", "title": "...", "deadline": "...", "why": "..."}],
        "insights": [{"icon": "⚠️", "title": "...", "description": "...", "metric": "..."}]
    }
    """
    
    # Extract key business metrics
    health_score_data = business_context.get('health_score', {})
    if isinstance(health_score_data, dict):
        health_score = health_score_data.get('score', 0)
        breakdown = health_score_data.get('breakdown', {})
    else:
        health_score = health_score_data if health_score_data else 0
        breakdown = {}
    
    alerts = business_context.get('alerts', [])
    signals = business_context.get('signals', [])
    
    # Step 1: Data Extraction Agent
    extracted_data = _extract_key_metrics(task_results, business_context)
    
    # Step 2: Visualization Agent - Create chart specs
    charts = _generate_charts(extracted_data, health_score, breakdown)
    
    # Step 3: Create comparison tables
    tables = _generate_tables(extracted_data, task_results)
    
    # Step 4: Action Agent - Generate actionable cards
    actions = _generate_action_cards(alerts, signals, extracted_data, health_score)
    
    # Step 5: Create KPI widgets
    kpis = _generate_kpis(health_score, breakdown, extracted_data)
    
    # Step 6: Generate insights with data
    insights = _generate_data_insights(extracted_data, alerts, signals)
    
    # Step 7: Quick summary (conversational but brief)
    summary = _generate_summary(health_score, alerts, extracted_data, user_message)
    
    return {
        "summary": summary,
        "kpis": kpis,
        "charts": charts,
        "tables": tables,
        "actions": actions,
        "insights": insights,
        "metadata": {
            "health_score": health_score,
            "alert_count": len(alerts),
            "signal_count": len(signals)
        }
    }


def _extract_key_metrics(task_results: Dict[str, Any], business_context: Dict[str, Any]) -> Dict[str, Any]:
    """Data Extraction Agent - Pull SPECIFIC details with client names, amounts, dates"""
    metrics = {
        "inventory": {},
        "revenue": {},
        "cash_flow": {},
        "customers": {},
        "orders": {},
        "raw_data": {}  # Store actual records for evidence
    }
    
    # Extract from task results - GET SPECIFIC RECORDS
    for task_id, result in task_results.items():
        if not isinstance(result, dict):
            continue
        
        # Store raw result for evidence generation
        metrics["raw_data"][task_id] = result
            
        if 'inventory' in task_id:
            metrics["inventory"].update({
                "total_items": result.get('total_items', 0),
                "total_value": result.get('total_value', 0),
                "low_stock_count": result.get('low_stock_count', 0),
                "top_products": result.get('top_products', []),
                "low_stock_items": result.get('low_stock_items', [])  # Actual items with names
            })
        
        elif 'revenue' in task_id:
            metrics["revenue"].update({
                "total": result.get('total_revenue', 0),
                "growth_rate": result.get('growth_rate', 0),
                "by_period": result.get('by_period', []),
                "top_customers": result.get('top_customers', [])  # Customer names + amounts
            })
        
        elif 'cash' in task_id or 'invoice' in task_id:
            # CRITICAL: Extract SPECIFIC invoice details with client names
            overdue_list = result.get('overdue_invoices', [])
            metrics["cash_flow"].update({
                "overdue_invoices": result.get('overdue_count', len(overdue_list)),
                "overdue_amount": result.get('overdue_amount', 0),
                "projected_negative_days": result.get('days_until_negative', None),
                "overdue_details": overdue_list  # THIS IS KEY: actual client names, amounts, due dates
            })
        
        elif 'order' in task_id:
            metrics["orders"].update({
                "total_orders": result.get('total_orders', 0),
                "avg_daily": result.get('avg_daily_orders', 0),
                "trend": result.get('trend', 'stable'),
                "recent_orders": result.get('recent_orders', [])  # Order history
            })
    
    return metrics


def _generate_charts(extracted_data: Dict[str, Any], health_score: int, breakdown: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Visualization Agent - Generate chart specifications"""
    charts = []
    
    # Chart 1: Health Score Breakdown
    if breakdown:
        charts.append({
            "type": "radialBar",
            "title": "Health Score Breakdown",
            "data": [
                {"category": "Revenue", "value": breakdown.get('revenue', 0), "color": "#10b981"},
                {"category": "Operations", "value": breakdown.get('operations', 0), "color": "#3b82f6"},
                {"category": "Customer", "value": breakdown.get('customer', 0), "color": "#8b5cf6"}
            ],
            "config": {
                "height": 200,
                "showLabels": True
            }
        })
    
    # Chart 2: Revenue Trend (if available)
    revenue_data = extracted_data.get('revenue', {})
    if revenue_data.get('by_period'):
        charts.append({
            "type": "line",
            "title": "Revenue Trend",
            "data": revenue_data['by_period'],
            "config": {
                "height": 180,
                "showGrid": True,
                "xAxis": "period",
                "yAxis": "amount"
            }
        })
    
    # Chart 3: Top Products (if inventory analysis)
    inventory_data = extracted_data.get('inventory', {})
    if inventory_data.get('top_products'):
        top_5 = inventory_data['top_products'][:5]
        charts.append({
            "type": "bar",
            "title": "Top 5 Products by Value",
            "data": [
                {"name": p.get('name', 'Unknown'), "value": p.get('value', 0)}
                for p in top_5
            ],
            "config": {
                "height": 200,
                "horizontal": True,
                "showValues": True
            }
        })
    
    return charts


def _generate_tables(extracted_data: Dict[str, Any], task_results: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Generate EVIDENCE tables with actual data records"""
    tables = []
    
    # Table 1: Overdue Invoices (EVIDENCE)
    cash_flow = extracted_data.get('cash_flow', {})
    overdue_details = cash_flow.get('overdue_details', [])
    if overdue_details:
        rows = []
        for invoice in overdue_details[:10]:  # Top 10
            rows.append({
                "client": invoice.get('customer_name', invoice.get('client_name', 'Unknown')),
                "invoice": invoice.get('invoice_id', invoice.get('id', '')),
                "amount": f"${invoice.get('amount', invoice.get('total', 0)):,.2f}",
                "due_date": invoice.get('due_date', ''),
                "days_overdue": invoice.get('days_overdue', 0),
                "status": "critical" if invoice.get('days_overdue', 0) > 60 else "warning"
            })
        
        if rows:
            tables.append({
                "title": "⚠️ Overdue Invoices - Evidence",
                "headers": ["Client", "Invoice", "Amount", "Due Date", "Days Overdue", "Status"],
                "rows": rows
            })
    
    # Table 2: Low Stock Items (EVIDENCE)
    inventory = extracted_data.get('inventory', {})
    low_stock_items = inventory.get('low_stock_items', [])
    if low_stock_items:
        rows = []
        for item in low_stock_items[:10]:
            rows.append({
                "product": item.get('product_name', item.get('name', 'Unknown')),
                "current": item.get('current_stock', item.get('quantity', 0)),
                "min_required": item.get('reorder_level', item.get('min_quantity', 0)),
                "shortage": item.get('reorder_level', 0) - item.get('current_stock', 0),
                "status": "critical" if item.get('current_stock', 0) == 0 else "warning"
            })
        
        if rows:
            tables.append({
                "title": "📦 Low Stock Items - Evidence",
                "headers": ["Product", "Current", "Min Required", "Shortage", "Status"],
                "rows": rows
            })
    
    # Table 3: Top Revenue Products (EVIDENCE)
    top_products = inventory.get('top_products', [])
    if top_products:
        rows = []
        for product in top_products[:10]:
            rows.append({
                "product": product.get('name', 'Unknown'),
                "revenue": f"${product.get('value', product.get('revenue', 0)):,.2f}",
                "units_sold": product.get('units', product.get('quantity', 0)),
                "status": "good"
            })
        
        if rows:
            tables.append({
                "title": "⭐ Top Revenue Products - Evidence",
                "headers": ["Product", "Revenue", "Units Sold", "Status"],
                "rows": rows
            })
    
    # Table 4: Key Metrics Summary
    revenue = extracted_data.get('revenue', {})
    if inventory or revenue or cash_flow:
        rows = []
        if inventory.get('total_items'):
            rows.append({
                "metric": "Inventory Items",
                "current": inventory['total_items'],
                "status": "warning" if inventory.get('low_stock_count', 0) > 0 else "good"
            })
        if revenue.get('total'):
            rows.append({
                "metric": "Revenue",
                "current": f"${revenue['total']:,.2f}",
                "status": "good" if revenue.get('growth_rate', 0) > 0 else "warning"
            })
        if cash_flow.get('overdue_invoices'):
            rows.append({
                "metric": "Overdue Invoices",
                "current": cash_flow['overdue_invoices'],
                "status": "critical" if cash_flow['overdue_invoices'] > 3 else "warning"
            })
        
        if rows:
            tables.append({
                "title": "📊 Key Metrics Summary",
                "headers": ["Metric", "Current", "Status"],
                "rows": rows
            })
    
    return tables


def _generate_action_cards(
    alerts: List[Dict[str, Any]],
    signals: List[Dict[str, Any]],
    extracted_data: Dict[str, Any],
    health_score: int
) -> List[Dict[str, Any]]:
    """Action Agent - Generate SPECIFIC actionable task cards with client names and details"""
    actions = []
    
    cash_flow = extracted_data.get('cash_flow', {})
    inventory = extracted_data.get('inventory', {})
    
    # Action 1: SPECIFIC cash flow actions with CLIENT NAMES
    overdue_details = cash_flow.get('overdue_details', [])
    if overdue_details:
        overdue_count = len(overdue_details)
        overdue_amount = cash_flow.get('overdue_amount', 0)
        days_until_neg = cash_flow.get('projected_negative_days')
        
        priority = "critical" if days_until_neg and days_until_neg <= 14 else "high"
        deadline = "Day 1-2" if priority == "critical" else "Day 1-3"
        
        # Build SPECIFIC client list with amounts
        client_list = []
        for invoice in overdue_details[:3]:  # Top 3
            client_name = invoice.get('customer_name', invoice.get('client_name', 'Unknown'))
            amount = invoice.get('amount', invoice.get('total', 0))
            days_overdue = invoice.get('days_overdue', 0)
            client_list.append({
                "name": client_name,
                "amount": amount,
                "days_overdue": days_overdue,
                "invoice_id": invoice.get('invoice_id', invoice.get('id', ''))
            })
        
        # Create action with SPECIFIC client details
        action_title = f"Contact {overdue_count} clients with overdue invoices"
        action_details = "\n".join([
            f"• {c['name']}: ${c['amount']:,.0f} ({c['days_overdue']} days overdue)"
            for c in client_list
        ])
        
        actions.append({
            "priority": priority,
            "title": action_title,
            "deadline": deadline,
            "why": f"${overdue_amount:,.0f} at risk" + (f", cash negative in {days_until_neg} days" if days_until_neg else ""),
            "metric": f"${overdue_amount:,.0f}",
            "icon": "💰",
            "details": action_details,  # SPECIFIC client breakdown
            "clients": client_list  # Structured data for rendering
        })
    
    # Action 2: SPECIFIC low stock items with PRODUCT NAMES
    low_stock_items = inventory.get('low_stock_items', [])
    if low_stock_items:
        low_stock_count = len(low_stock_items)
        
        # Build SPECIFIC product list
        product_list = []
        for item in low_stock_items[:5]:  # Top 5
            product_name = item.get('product_name', item.get('name', 'Unknown'))
            current_stock = item.get('current_stock', item.get('quantity', 0))
            reorder_level = item.get('reorder_level', item.get('min_quantity', 0))
            product_list.append({
                "name": product_name,
                "current": current_stock,
                "min": reorder_level
            })
        
        product_details = "\n".join([
            f"• {p['name']}: {p['current']} units (min: {p['min']})"
            for p in product_list
        ])
        
        actions.append({
            "priority": "medium",
            "title": f"Reorder {low_stock_count} low-stock items",
            "deadline": "Day 3-5",
            "why": "Prevent stockouts and lost sales",
            "metric": f"{low_stock_count} items",
            "icon": "📦",
            "details": product_details,
            "products": product_list
        })
    
    # Action 3: Health score improvement
    if health_score < 60:
        actions.append({
            "priority": "high",
            "title": "Address critical alerts to improve health score",
            "deadline": "This week",
            "why": f"Current score {health_score}/100 needs improvement",
            "metric": f"{health_score}/100",
            "icon": "🎯"
        })
    
    # Limit to top 5 actions
    return sorted(actions, key=lambda x: {"critical": 0, "high": 1, "medium": 2}.get(x['priority'], 3))[:5]


def _generate_kpis(health_score: int, breakdown: Dict[str, Any], extracted_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Generate KPI widget data"""
    kpis = [
        {
            "label": "Health Score",
            "value": health_score,
            "unit": "/100",
            "trend": "down" if health_score < 50 else "stable",
            "color": "red" if health_score < 40 else "yellow" if health_score < 70 else "green"
        }
    ]
    
    revenue = extracted_data.get('revenue', {})
    if revenue.get('total'):
        kpis.append({
            "label": "Revenue",
            "value": f"${revenue['total']/1000:.1f}k",
            "trend": "up" if revenue.get('growth_rate', 0) > 0 else "down",
            "color": "green" if revenue.get('growth_rate', 0) > 0 else "red"
        })
    
    cash_flow = extracted_data.get('cash_flow', {})
    if cash_flow.get('overdue_amount'):
        kpis.append({
            "label": "Overdue",
            "value": f"${cash_flow['overdue_amount']/1000:.1f}k",
            "trend": "critical",
            "color": "red"
        })
    
    inventory = extracted_data.get('inventory', {})
    if inventory.get('total_items'):
        kpis.append({
            "label": "Inventory",
            "value": inventory['total_items'],
            "unit": " items",
            "trend": "stable",
            "color": "blue"
        })
    
    return kpis


def _generate_data_insights(
    extracted_data: Dict[str, Any],
    alerts: List[Dict[str, Any]],
    signals: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """Generate insights with specific data points"""
    insights = []
    
    cash_flow = extracted_data.get('cash_flow', {})
    if cash_flow.get('overdue_invoices', 0) > 0:
        insights.append({
            "icon": "⚠️",
            "type": "warning",
            "title": "Cash Flow Risk",
            "description": f"{cash_flow['overdue_invoices']} invoices overdue, totaling ${cash_flow.get('overdue_amount', 0):,.0f}",
            "metric": f"${cash_flow.get('overdue_amount', 0):,.0f}",
            "action": "Contact clients immediately"
        })
    
    inventory = extracted_data.get('inventory', {})
    if inventory.get('low_stock_count', 0) > 0:
        insights.append({
            "icon": "📦",
            "type": "info",
            "title": "Stock Alert",
            "description": f"{inventory['low_stock_count']} items below minimum threshold",
            "metric": f"{inventory['low_stock_count']} items",
            "action": "Review reorder points"
        })
    
    revenue = extracted_data.get('revenue', {})
    if revenue.get('growth_rate', 0) > 5:
        insights.append({
            "icon": "📈",
            "type": "positive",
            "title": "Revenue Growth",
            "description": f"Revenue up {revenue['growth_rate']:.1f}% vs last period",
            "metric": f"+{revenue['growth_rate']:.1f}%",
            "action": "Maintain momentum"
        })
    
    return insights[:4]  # Limit to 4 key insights


def _generate_summary(
    health_score: int,
    alerts: List[Dict[str, Any]],
    extracted_data: Dict[str, Any],
    user_message: str
) -> str:
    """Generate brief conversational summary (2-3 sentences max)"""
    cash_flow = extracted_data.get('cash_flow', {})
    
    # Build context-aware summary
    priority_issue = None
    if cash_flow.get('overdue_invoices', 0) > 0:
        priority_issue = f"{cash_flow['overdue_invoices']} overdue invoices worth ${cash_flow.get('overdue_amount', 0):,.0f}"
    elif health_score < 40:
        priority_issue = f"health score at {health_score}/100"
    
    if priority_issue:
        summary = f"Your top priority: {priority_issue}. "
    else:
        summary = f"With a health score of {health_score}/100, "
    
    summary += f"I've identified {len(alerts)} areas needing attention. Focus on the action cards below for immediate impact."
    
    return summary
