"""
Advanced Inventory Optimizer using OR-Tools
Production-grade optimization with linear programming
"""
from typing import Dict, List, Any, Optional
import json
import uuid
from datetime import datetime, timezone

try:
    from ortools.linear_solver import pywraplp
    ORTOOLS_AVAILABLE = True
except ImportError:
    ORTOOLS_AVAILABLE = False


class ORToolsOptimizer:
    """Advanced inventory optimization using Google OR-Tools"""
    
    def __init__(self, backend):
        """Initialize with PostgreSQL backend"""
        self.backend = backend
        if not ORTOOLS_AVAILABLE:
            raise ImportError("OR-Tools not installed. Run: pip install ortools")
    
    async def optimize_inventory_lp(
        self,
        tenant_id: str,
        objective: str = "minimize_cost",
        constraints: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Optimize inventory using Linear Programming
        
        Objective: Minimize total cost = holding_cost + ordering_cost + stockout_cost
        
        Constraints:
        - Inventory balance equations
        - Capacity limits
        - Service level requirements
        - Budget constraints
        
        Args:
            tenant_id: Tenant identifier
            objective: Optimization goal
            constraints: User-defined constraints
        
        Returns:
            Optimal order quantities and inventory levels
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
                
                # Get detailed inventory data
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
                forecast_data = forecast_row[0] if forecast_row else {}
                
                # Optimization parameters
                holding_cost_rate = constraints.get('holding_cost_rate', 0.2)  # 20% annual
                order_cost = constraints.get('order_cost', 50)  # $50 per order
                stockout_cost_multiplier = constraints.get('stockout_cost_multiplier', 5)  # 5x unit cost
                service_level = constraints.get('service_level', 0.95)  # 95%
                budget_limit = constraints.get('budget_limit', float('inf'))  # No limit
                
                # Create LP solver
                solver = pywraplp.Solver.CreateSolver('GLOP')
                if not solver:
                    return {"error": "Could not create LP solver"}
                
                # Decision variables and constraints
                order_vars = {}  # Order quantities for each SKU
                inventory_vars = {}  # Target inventory levels
                recommendations = []
                
                total_cost = 0
                
                for item in inventory_items:
                    sku = item.get('sku', '')
                    current_stock = float(item.get('current_stock', 0))
                    min_stock = float(item.get('min_stock', 0))
                    max_stock = float(item.get('max_stock', 0))
                    unit_cost = float(item.get('unit_cost', 0))
                    
                    # Get forecasted demand
                    if sku in forecast_data:
                        sku_forecast = forecast_data[sku]
                        predictions = sku_forecast.get('predictions', [])
                        avg_weekly_demand = sum(p['predicted_quantity'] for p in predictions) / len(predictions) if predictions else 0
                    else:
                        # Estimate from current stock
                        avg_weekly_demand = current_stock / 4  # Assume monthly turnover
                    
                    # Decision variables
                    order_qty = solver.NumVar(0, max_stock, f'order_{sku}')
                    target_inv = solver.NumVar(min_stock, max_stock, f'inventory_{sku}')
                    
                    order_vars[sku] = order_qty
                    inventory_vars[sku] = target_inv
                    
                    # Costs
                    holding_cost_per_unit = unit_cost * holding_cost_rate / 52  # Weekly
                    stockout_cost_per_unit = unit_cost * stockout_cost_multiplier
                    
                    # Inventory balance: current + order = target
                    solver.Add(target_inv == current_stock + order_qty - avg_weekly_demand)
                    
                    # Service level constraint (safety stock)
                    z_score = 1.65 if service_level >= 0.95 else 1.28
                    demand_std = avg_weekly_demand * 0.2  # Assume 20% variance
                    safety_stock = z_score * demand_std
                    solver.Add(target_inv >= safety_stock)
                    
                    # Cost components (linearized for LP)
                    # Holding cost
                    holding_cost = holding_cost_per_unit * target_inv
                    
                    # Ordering cost (fixed cost when order > 0, approximated)
                    # For LP, we use continuous approximation
                    ordering_cost = order_cost * (order_qty / (avg_weekly_demand * 4 + 1))
                    
                    # Stockout cost (penalize insufficient inventory)
                    # Using slack variable for stockout
                    stockout = solver.NumVar(0, solver.infinity(), f'stockout_{sku}')
                    solver.Add(stockout >= avg_weekly_demand - target_inv)
                    stockout_cost = stockout_cost_per_unit * stockout
                    
                    total_cost += holding_cost + ordering_cost + stockout_cost
                
                # Budget constraint
                total_order_cost = sum(
                    order_vars[item['sku']] * float(item['unit_cost'])
                    for item in inventory_items
                )
                solver.Add(total_order_cost <= budget_limit)
                
                # Objective: Minimize total cost
                solver.Minimize(total_cost)
                
                # Solve
                status = solver.Solve()
                
                if status == pywraplp.Solver.OPTIMAL:
                    solver_status = 'optimal'
                    objective_value = solver.Objective().Value()
                elif status == pywraplp.Solver.FEASIBLE:
                    solver_status = 'feasible'
                    objective_value = solver.Objective().Value()
                else:
                    solver_status = 'infeasible'
                    objective_value = None
                    return {
                        "error": "Optimization problem is infeasible",
                        "solver_status": solver_status
                    }
                
                # Extract solution
                total_savings = 0.0
                for item in inventory_items:
                    sku = item.get('sku', '')
                    current_stock = float(item.get('current_stock', 0))
                    unit_cost = float(item.get('unit_cost', 0))
                    
                    optimal_order = order_vars[sku].solution_value()
                    optimal_inventory = inventory_vars[sku].solution_value()
                    
                    # Determine action
                    if optimal_order > 10:  # Threshold for ordering
                        action = "ORDER_NOW"
                        order_qty = optimal_order
                    elif current_stock > optimal_inventory * 1.2:
                        action = "REDUCE_STOCK"
                        order_qty = 0
                        excess = current_stock - optimal_inventory
                        potential_saving = excess * unit_cost * holding_cost_rate / 52
                        total_savings += potential_saving
                    else:
                        action = "MAINTAIN"
                        order_qty = 0
                    
                    recommendations.append({
                        'sku': sku,
                        'product_name': item.get('product_name', ''),
                        'current_stock': current_stock,
                        'optimal_order_qty': round(optimal_order, 2),
                        'target_inventory': round(optimal_inventory, 2),
                        'action': action,
                        'order_quantity': round(order_qty, 2) if order_qty > 0 else None,
                        'potential_saving': round(total_savings / len(inventory_items), 2)
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
                        'inventory_lp',
                        json.dumps(constraints),
                        json.dumps(recommendations),
                        objective_value,
                        solver_status
                    ]
                )
                conn.commit()
                
                return {
                    'optimization_id': optimization_id,
                    'objective': objective,
                    'solver_status': solver_status,
                    'objective_value': round(objective_value, 2),
                    'recommendations': recommendations,
                    'total_potential_savings': round(total_savings, 2),
                    'items_analyzed': len(recommendations),
                    'actions_required': sum(1 for r in recommendations if r['action'] in ['ORDER_NOW', 'REDUCE_STOCK']),
                    'generated_at': datetime.now(timezone.utc).isoformat()
                }
