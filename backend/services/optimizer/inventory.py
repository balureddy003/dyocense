"""
Inventory Optimizer Service
Simple optimization for order quantities and reorder points
Production version should use OR-Tools or PuLP for LP/MIP
"""
from typing import Dict, List, Any, Optional
import json
import uuid
from datetime import datetime, timezone


class InventoryOptimizer:
    """Simple inventory optimization service"""
    
    def __init__(self, backend):
        """Initialize with PostgreSQL backend"""
        self.backend = backend
    
    def _calculate_eoq(self, annual_demand: float, order_cost: float, holding_cost: float) -> float:
        """
        Calculate Economic Order Quantity (EOQ)
        EOQ = sqrt((2 * D * S) / H)
        where D = annual demand, S = order cost, H = holding cost per unit
        """
        if holding_cost == 0:
            return 0
        return ((2 * annual_demand * order_cost) / holding_cost) ** 0.5
    
    def _calculate_reorder_point(
        self, 
        avg_daily_demand: float, 
        lead_time_days: float, 
        safety_stock: float
    ) -> float:
        """
        Calculate Reorder Point (ROP)
        ROP = (Average Daily Demand × Lead Time) + Safety Stock
        """
        return (avg_daily_demand * lead_time_days) + safety_stock
    
    async def optimize_inventory(
        self,
        tenant_id: str,
        objective: str = "minimize_cost",  # minimize_cost, maximize_service_level
        constraints: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Optimize inventory levels and order quantities
        
        Args:
            tenant_id: Tenant identifier
            objective: Optimization objective
            constraints: Optional constraints (budget, space, service level)
        
        Returns:
            Optimization results with recommendations
        """
        constraints = constraints or {}
        
        with self.backend.get_connection() as conn:
            with conn.cursor() as cur:
                # Get inventory metrics
                cur.execute(
                    """
                    SELECT extra_data FROM business_metrics 
                    WHERE tenant_id = %s AND metric_name = 'total_inventory_value'
                    ORDER BY timestamp DESC LIMIT 1
                    """,
                    [tenant_id]
                )
                inv_row = cur.fetchone()
                
                # Get demand forecast
                cur.execute(
                    """
                    SELECT predictions FROM forecasts 
                    WHERE tenant_id = %s AND metric_name = 'demand'
                    ORDER BY created_at DESC LIMIT 1
                    """,
                    [tenant_id]
                )
                forecast_row = cur.fetchone()
                
                if not inv_row:
                    return {"error": "No inventory data found. Run ELT pipeline first."}
                
                # Get detailed inventory and demand data
                source_id = inv_row[0].get('source_id')
                cur.execute(
                    """
                    SELECT data FROM raw_connector_data 
                    WHERE source_id = %s 
                    ORDER BY ingested_at DESC LIMIT 1
                    """,
                    [source_id]
                )
                raw_inv = cur.fetchone()
                
                if not raw_inv:
                    return {"error": "Inventory source data not found"}
                
                inventory_items = raw_inv[0].get('sample_rows', [])
                
                # Get demand data
                forecast_data = forecast_row[0] if forecast_row else {}
                
                # Optimization parameters (simplified)
                order_cost = constraints.get('order_cost', 50)  # $50 per order
                holding_cost_rate = constraints.get('holding_cost_rate', 0.2)  # 20% annual
                lead_time_days = constraints.get('lead_time_days', 7)  # 1 week
                service_level = constraints.get('service_level', 0.95)  # 95%
                
                recommendations = []
                total_savings = 0.0
                
                for item in inventory_items:
                    sku = item.get('sku', '')
                    current_stock = float(item.get('current_stock', 0))
                    min_stock = float(item.get('min_stock', 0))
                    max_stock = float(item.get('max_stock', 0))
                    unit_cost = float(item.get('unit_cost', 0))
                    
                    # Calculate annual demand from forecast
                    if sku in forecast_data:
                        sku_forecast = forecast_data[sku]
                        predictions = sku_forecast.get('predictions', [])
                        # Estimate weekly demand from forecast
                        avg_weekly_demand = sum(p['predicted_quantity'] for p in predictions) / len(predictions) if predictions else 0
                        annual_demand = avg_weekly_demand * 52  # 52 weeks
                    else:
                        # Fallback: use current stock turnover estimate
                        annual_demand = current_stock * 12  # Assume monthly turnover
                    
                    # Calculate holding cost per unit
                    holding_cost = unit_cost * holding_cost_rate
                    
                    # Calculate EOQ
                    eoq = self._calculate_eoq(annual_demand, order_cost, holding_cost)
                    
                    # Calculate safety stock (simple: z-score * std dev of demand)
                    # For 95% service level, z-score ≈ 1.65
                    z_score = 1.65 if service_level >= 0.95 else 1.28
                    demand_std = annual_demand * 0.2  # Assume 20% variance
                    safety_stock = z_score * (demand_std / 52) * (lead_time_days / 7) ** 0.5
                    
                    # Calculate reorder point
                    avg_daily_demand = annual_demand / 365
                    rop = self._calculate_reorder_point(avg_daily_demand, lead_time_days, safety_stock)
                    
                    # Determine action
                    action = None
                    potential_saving = 0.0
                    
                    if current_stock < rop:
                        action = "ORDER_NOW"
                        order_qty = eoq
                        potential_saving = 0  # Avoid stockout
                    elif current_stock > max_stock * 0.9:
                        action = "REDUCE_STOCK"
                        order_qty = 0
                        # Savings from reduced holding cost
                        excess = current_stock - rop
                        potential_saving = excess * holding_cost
                    else:
                        action = "MAINTAIN"
                        order_qty = 0
                    
                    total_savings += potential_saving
                    
                    recommendations.append({
                        'sku': sku,
                        'product_name': item.get('product_name', ''),
                        'current_stock': current_stock,
                        'optimal_order_qty': round(eoq, 2),
                        'reorder_point': round(rop, 2),
                        'safety_stock': round(safety_stock, 2),
                        'action': action,
                        'order_quantity': round(order_qty, 2) if order_qty > 0 else None,
                        'potential_saving': round(potential_saving, 2),
                        'annual_demand_estimate': round(annual_demand, 2)
                    })
                
                # Store optimization run
                optimization_id = str(uuid.uuid4())
                cur.execute(
                    """
                    INSERT INTO optimization_runs 
                    (run_id, tenant_id, problem_type, input_data, 
                     solution, objective_value, solver_status, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, NOW())
                    """,
                    [
                        optimization_id,
                        tenant_id,
                        'inventory_optimization',
                        json.dumps(constraints),
                        json.dumps(recommendations),
                        total_savings,
                        'optimal'
                    ]
                )
                conn.commit()
                
                return {
                    'optimization_id': optimization_id,
                    'objective': objective,
                    'recommendations': recommendations,
                    'total_potential_savings': round(total_savings, 2),
                    'items_analyzed': len(recommendations),
                    'actions_required': sum(1 for r in recommendations if r['action'] in ['ORDER_NOW', 'REDUCE_STOCK']),
                    'generated_at': datetime.now(timezone.utc).isoformat()
                }
