"""
Analysis Tools - Decoupled Business Logic

Business-specific analysis functions that can be registered with ToolExecutor.
Each tool is independent and can be:
- Tested in isolation
- Swapped per tenant/industry
- Extended without modifying coach code
"""
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


def analyze_inventory_data(business_context: Dict[str, Any], **kwargs) -> Optional[Dict[str, Any]]:
    """
    Analyze inventory data and provide insights
    
    Industry-agnostic implementation that adapts to business terminology:
    - Retail/Ecommerce: products, SKUs
    - Healthcare: supplies, medical items
    - Manufacturing: raw materials, components
    - Restaurant: ingredients, menu items
    - Services: resources, assets
    """
    try:
        # Get industry-specific terminology
        terminology = business_context.get("terminology", {})
        items_term = terminology.get("items", "items")
        
        metrics = business_context.get("metrics", {})
        total_items = metrics.get("total_inventory_items", 0)
        total_qty = metrics.get("total_inventory_quantity", 0)
        total_value = metrics.get("total_inventory_value", 0)
        low_stock = metrics.get("low_stock_items", 0)
        out_of_stock = metrics.get("out_of_stock_items", 0)
        
        if total_items == 0:
            logger.warning("No inventory data available")
            return None
        
        # Calculate stock health percentages
        in_stock = total_items - low_stock - out_of_stock
        in_stock_pct = (in_stock / total_items * 100) if total_items > 0 else 0
        low_stock_pct = (low_stock / total_items * 100) if total_items > 0 else 0
        out_of_stock_pct = (out_of_stock / total_items * 100) if total_items > 0 else 0
        
        # Average value per item
        avg_value = (total_value / total_items) if total_items > 0 else 0
        
        # Identify critical issues
        critical_issues = []
        if out_of_stock_pct > 5:
            critical_issues.append(f"High out-of-stock rate: {out_of_stock_pct:.1f}%")
        if low_stock_pct > 20:
            critical_issues.append(f"Many items running low: {low_stock_pct:.1f}%")
        
        # Generate recommendations
        recommendations = []
        if out_of_stock > 0:
            recommendations.append(f"Restock {out_of_stock} out-of-stock items immediately")
        if low_stock > 0:
            recommendations.append(f"Review reorder points for {low_stock} low-stock items")
        if avg_value > 100:
            recommendations.append("High-value inventory - consider ABC analysis for optimization")
        
        return {
            "total_items": total_items,
            "total_quantity": total_qty,
            "total_value": total_value,
            "avg_value_per_sku": avg_value,
            "stock_health": {
                "in_stock": {"count": in_stock, "percentage": round(in_stock_pct, 1)},
                "low_stock": {"count": low_stock, "percentage": round(low_stock_pct, 1)},
                "out_of_stock": {"count": out_of_stock, "percentage": round(out_of_stock_pct, 1)},
            },
            "critical_issues": critical_issues,
            "recommendations": recommendations
        }
    except Exception as e:
        logger.error(f"Error analyzing inventory data: {e}", exc_info=True)
        return None


def analyze_revenue_data(business_context: Dict[str, Any], **kwargs) -> Optional[Dict[str, Any]]:
    """
    Analyze revenue trends and patterns
    
    Industry-specific implementations:
    - SaaS: analyze_recurring_revenue()
    - Retail: analyze_sales_by_category()
    - Services: analyze_billable_hours()
    """
    try:
        metrics = business_context.get("metrics", {})
        revenue_30d = metrics.get("revenue_last_30_days", 0)
        orders_30d = metrics.get("orders_last_30_days", 0)
        avg_order_value = metrics.get("avg_order_value", 0)
        
        if revenue_30d == 0:
            logger.warning("No revenue data available")
            return None
        
        # Calculate key metrics
        revenue_per_day = revenue_30d / 30 if revenue_30d > 0 else 0
        
        return {
            "revenue_30d": revenue_30d,
            "orders_30d": orders_30d,
            "avg_order_value": avg_order_value,
            "revenue_per_day": revenue_per_day,
            "insights": [
                f"Average daily revenue: ${revenue_per_day:,.2f}",
                f"Average order value: ${avg_order_value:,.2f}"
            ]
        }
    except Exception as e:
        logger.error(f"Error analyzing revenue data: {e}", exc_info=True)
        return None


def analyze_customer_data(business_context: Dict[str, Any], **kwargs) -> Optional[Dict[str, Any]]:
    """
    Analyze customer metrics and segments
    
    Industry-specific implementations:
    - B2B: analyze_account_health()
    - B2C: analyze_customer_lifetime_value()
    - Subscription: analyze_churn_risk()
    """
    try:
        metrics = business_context.get("metrics", {})
        total_customers = metrics.get("total_customers", 0)
        vip_customers = metrics.get("vip_customers", 0)
        repeat_rate = metrics.get("repeat_customer_rate", 0)
        
        if total_customers == 0:
            logger.warning("No customer data available")
            return None
        
        vip_pct = (vip_customers / total_customers * 100) if total_customers > 0 else 0
        
        return {
            "total_customers": total_customers,
            "vip_customers": vip_customers,
            "vip_percentage": round(vip_pct, 1),
            "repeat_rate": repeat_rate,
            "insights": [
                f"{vip_pct:.1f}% VIP customers driving loyalty",
                f"{repeat_rate}% repeat purchase rate"
            ]
        }
    except Exception as e:
        logger.error(f"Error analyzing customer data: {e}", exc_info=True)
        return None


def analyze_health_metrics(business_context: Dict[str, Any], **kwargs) -> Optional[Dict[str, Any]]:
    """
    Analyze overall business health
    
    Cross-industry health metrics with domain-specific weights
    """
    try:
        metrics = business_context.get("metrics", {})
        
        # Calculate health score components
        health_components = []
        
        # Revenue health
        revenue_30d = metrics.get("revenue_last_30_days", 0)
        if revenue_30d > 0:
            health_components.append({"name": "Revenue", "score": min(100, revenue_30d / 1000)})
        
        # Inventory health (SMB-specific)
        total_items = metrics.get("total_inventory_items", 0)
        out_of_stock = metrics.get("out_of_stock_items", 0)
        if total_items > 0:
            inventory_health = ((total_items - out_of_stock) / total_items) * 100
            health_components.append({"name": "Inventory", "score": inventory_health})
        
        # Customer health
        repeat_rate = metrics.get("repeat_customer_rate", 0)
        if repeat_rate > 0:
            health_components.append({"name": "Customer Loyalty", "score": repeat_rate})
        
        # Calculate overall score
        overall_score = sum(c["score"] for c in health_components) / len(health_components) if health_components else 0
        
        return {
            "overall_score": round(overall_score, 1),
            "components": health_components,
            "status": "healthy" if overall_score >= 70 else "needs_attention" if overall_score >= 40 else "critical"
        }
    except Exception as e:
        logger.error(f"Error analyzing health metrics: {e}", exc_info=True)
        return None
