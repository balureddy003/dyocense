"""
Inventory Optimization using OR-Tools

Solves inventory management problems:
- Economic Order Quantity (EOQ)
- Safety stock calculation
- Reorder point optimization
- Multi-product inventory optimization
"""

from __future__ import annotations

import logging
from typing import Any
from datetime import datetime, timedelta

import numpy as np
from ortools.linear_solver import pywraplp

logger = logging.getLogger(__name__)


class InventoryOptimizer:
    """
    Inventory optimization using OR-Tools.
    
    Methods:
    - calculate_eoq(): Economic Order Quantity
    - calculate_safety_stock(): Safety stock for service level
    - optimize_reorder_point(): Optimal reorder point
    - optimize_multi_product(): Multi-product optimization with constraints
    """
    
    def __init__(self):
        """Initialize optimizer."""
        self.logger = logging.getLogger(__name__)
    
    def calculate_eoq(
        self,
        annual_demand: float,
        order_cost: float,
        holding_cost_per_unit: float
    ) -> dict[str, Any]:
        """
        Calculate Economic Order Quantity (EOQ).
        
        EOQ Formula: sqrt((2 * D * S) / H)
        Where:
        - D = Annual demand (units)
        - S = Order cost per order ($)
        - H = Holding cost per unit per year ($)
        
        Args:
            annual_demand: Annual demand in units
            order_cost: Cost per order ($)
            holding_cost_per_unit: Annual holding cost per unit ($)
        
        Returns:
            Dict with EOQ, number of orders, and total cost
        """
        if annual_demand <= 0 or order_cost <= 0 or holding_cost_per_unit <= 0:
            raise ValueError("All inputs must be positive")
        
        # EOQ formula
        eoq = np.sqrt((2 * annual_demand * order_cost) / holding_cost_per_unit)
        
        # Number of orders per year
        num_orders = annual_demand / eoq
        
        # Total cost
        ordering_cost = num_orders * order_cost
        holding_cost = (eoq / 2) * holding_cost_per_unit
        total_cost = ordering_cost + holding_cost
        
        # Order frequency (days between orders)
        days_between_orders = 365 / num_orders
        
        self.logger.info(
            f"EOQ: {eoq:.1f} units, Orders/year: {num_orders:.1f}, "
            f"Total cost: ${total_cost:.2f}"
        )
        
        return {
            "eoq": round(eoq, 1),
            "num_orders_per_year": round(num_orders, 1),
            "days_between_orders": round(days_between_orders, 1),
            "total_annual_cost": round(total_cost, 2),
            "ordering_cost": round(ordering_cost, 2),
            "holding_cost": round(holding_cost, 2),
            "recommendation": f"Order {round(eoq, 1)} units every {round(days_between_orders, 1)} days"
        }
    
    def calculate_safety_stock(
        self,
        avg_daily_demand: float,
        demand_std_dev: float,
        lead_time_days: float,
        service_level: float = 0.95
    ) -> dict[str, Any]:
        """
        Calculate safety stock for given service level.
        
        Safety Stock = Z * σ_d * sqrt(L)
        Where:
        - Z = Z-score for service level
        - σ_d = Standard deviation of daily demand
        - L = Lead time in days
        
        Args:
            avg_daily_demand: Average daily demand
            demand_std_dev: Standard deviation of daily demand
            lead_time_days: Lead time in days
            service_level: Target service level (0.0 to 1.0)
        
        Returns:
            Dict with safety stock and reorder point
        """
        from scipy.stats import norm
        
        # Z-score for service level
        z_score = norm.ppf(service_level)
        
        # Safety stock formula
        safety_stock = z_score * demand_std_dev * np.sqrt(lead_time_days)
        
        # Reorder point = (avg daily demand × lead time) + safety stock
        reorder_point = (avg_daily_demand * lead_time_days) + safety_stock
        
        # Expected stockouts per year (for comparison)
        stockout_probability = 1 - service_level
        orders_per_year = 365 / lead_time_days
        expected_stockouts = stockout_probability * orders_per_year
        
        self.logger.info(
            f"Safety stock: {safety_stock:.1f} units, "
            f"Reorder point: {reorder_point:.1f}, "
            f"Service level: {service_level:.1%}"
        )
        
        return {
            "safety_stock": round(safety_stock, 1),
            "reorder_point": round(reorder_point, 1),
            "service_level": service_level,
            "z_score": round(z_score, 2),
            "expected_stockouts_per_year": round(expected_stockouts, 2),
            "recommendation": f"Maintain {round(safety_stock, 1)} units safety stock, reorder at {round(reorder_point, 1)} units"
        }
    
    def optimize_multi_product(
        self,
        products: list[dict[str, Any]],
        budget_constraint: float,
        storage_constraint: float
    ) -> dict[str, Any]:
        """
        Optimize inventory for multiple products with constraints.
        
        Minimizes total cost while satisfying:
        - Budget constraint (max total investment)
        - Storage constraint (max warehouse capacity)
        - Demand satisfaction (service level)
        
        Args:
            products: List of product dicts with keys:
                - name: Product name
                - annual_demand: Units per year
                - unit_cost: Cost per unit ($)
                - order_cost: Cost per order ($)
                - holding_cost_rate: Holding cost as % of unit cost
                - storage_space: Storage space per unit (sq ft)
            budget_constraint: Max budget for inventory ($)
            storage_constraint: Max storage space (sq ft)
        
        Returns:
            Optimization result with order quantities and costs
        """
        if not products:
            raise ValueError("Products list cannot be empty")
        
        self.logger.info(
            f"Optimizing inventory for {len(products)} products, "
            f"Budget: ${budget_constraint:,.0f}, Storage: {storage_constraint:,.0f} sq ft"
        )
        
        # Create OR-Tools solver
        solver = pywraplp.Solver.CreateSolver('SCIP')
        if not solver:
            raise RuntimeError("SCIP solver not available")
        
        # Decision variables: order quantity for each product
        order_quantities = {}
        for i, product in enumerate(products):
            # Q_i >= 0
            order_quantities[i] = solver.NumVar(
                0,
                solver.infinity(),
                f"Q_{product['name']}"
            )
        
        # Objective: Minimize total cost
        # Total cost = Σ (ordering cost + holding cost)
        # Ordering cost = (D_i / Q_i) * S_i
        # Holding cost = (Q_i / 2) * h_i
        objective = solver.Objective()
        
        for i, product in enumerate(products):
            Q = order_quantities[i]
            D = product['annual_demand']
            S = product['order_cost']
            h = product['unit_cost'] * product['holding_cost_rate']
            
            # Linearize the objective (approximate for demonstration)
            # In practice, would use EOQ as initial guess
            eoq_estimate = np.sqrt((2 * D * S) / h)
            
            # Ordering cost coefficient (linearized around EOQ)
            ordering_coef = -D * S / (eoq_estimate ** 2)
            
            # Holding cost coefficient
            holding_coef = h / 2
            
            objective.SetCoefficient(Q, ordering_coef + holding_coef)
        
        objective.SetMinimization()
        
        # Constraint 1: Budget
        # Σ (Q_i * unit_cost_i) <= budget
        budget_constraint_obj = solver.Constraint(0, budget_constraint)
        for i, product in enumerate(products):
            budget_constraint_obj.SetCoefficient(
                order_quantities[i],
                product['unit_cost']
            )
        
        # Constraint 2: Storage space
        # Σ (Q_i * storage_space_i) <= storage
        storage_constraint_obj = solver.Constraint(0, storage_constraint)
        for i, product in enumerate(products):
            storage_constraint_obj.SetCoefficient(
                order_quantities[i],
                product['storage_space']
            )
        
        # Constraint 3: Minimum order quantities (optional)
        # Q_i >= min_order_qty_i
        for i, product in enumerate(products):
            min_qty = product.get('min_order_qty', 1)
            solver.Add(order_quantities[i] >= min_qty)
        
        # Solve
        status = solver.Solve()
        
        if status == pywraplp.Solver.OPTIMAL:
            self.logger.info("Optimal solution found")
            
            results = []
            total_cost = 0
            total_budget_used = 0
            total_storage_used = 0
            
            for i, product in enumerate(products):
                Q = order_quantities[i].solution_value()
                D = product['annual_demand']
                S = product['order_cost']
                h = product['unit_cost'] * product['holding_cost_rate']
                
                # Calculate costs
                num_orders = D / Q if Q > 0 else 0
                ordering_cost = num_orders * S if Q > 0 else 0
                holding_cost = (Q / 2) * h
                product_total_cost = ordering_cost + holding_cost
                
                budget_used = Q * product['unit_cost']
                storage_used = Q * product['storage_space']
                
                total_cost += product_total_cost
                total_budget_used += budget_used
                total_storage_used += storage_used
                
                results.append({
                    "product": product['name'],
                    "order_quantity": round(Q, 1),
                    "num_orders_per_year": round(num_orders, 1),
                    "ordering_cost": round(ordering_cost, 2),
                    "holding_cost": round(holding_cost, 2),
                    "total_cost": round(product_total_cost, 2),
                    "budget_used": round(budget_used, 2),
                    "storage_used": round(storage_used, 1)
                })
            
            return {
                "status": "optimal",
                "products": results,
                "total_cost": round(total_cost, 2),
                "total_budget_used": round(total_budget_used, 2),
                "total_storage_used": round(total_storage_used, 1),
                "budget_utilization": round(total_budget_used / budget_constraint, 2),
                "storage_utilization": round(total_storage_used / storage_constraint, 2),
                "solver_time_ms": solver.wall_time()
            }
        
        elif status == pywraplp.Solver.FEASIBLE:
            self.logger.warning("Feasible solution found (not optimal)")
            return {
                "status": "feasible",
                "message": "Found feasible solution but not proven optimal"
            }
        
        else:
            self.logger.error("No solution found")
            return {
                "status": "infeasible",
                "message": "No feasible solution exists with given constraints"
            }
    
    def optimize_reorder_point(
        self,
        avg_daily_demand: float,
        demand_std_dev: float,
        lead_time_days: float,
        lead_time_std_dev: float,
        service_level: float = 0.95
    ) -> dict[str, Any]:
        """
        Calculate optimal reorder point with variable lead time.
        
        Accounts for uncertainty in both demand and lead time.
        
        Args:
            avg_daily_demand: Average daily demand
            demand_std_dev: Standard deviation of daily demand
            lead_time_days: Average lead time in days
            lead_time_std_dev: Standard deviation of lead time
            service_level: Target service level (0.0 to 1.0)
        
        Returns:
            Dict with reorder point and safety stock
        """
        from scipy.stats import norm
        
        # Z-score for service level
        z_score = norm.ppf(service_level)
        
        # Combined standard deviation (accounting for both uncertainties)
        # σ_total = sqrt((L * σ_d²) + (D² * σ_L²))
        variance_demand = lead_time_days * (demand_std_dev ** 2)
        variance_lead_time = (avg_daily_demand ** 2) * (lead_time_std_dev ** 2)
        combined_std_dev = np.sqrt(variance_demand + variance_lead_time)
        
        # Safety stock with variable lead time
        safety_stock = z_score * combined_std_dev
        
        # Reorder point
        reorder_point = (avg_daily_demand * lead_time_days) + safety_stock
        
        self.logger.info(
            f"Reorder point (variable lead time): {reorder_point:.1f} units, "
            f"Safety stock: {safety_stock:.1f}"
        )
        
        return {
            "reorder_point": round(reorder_point, 1),
            "safety_stock": round(safety_stock, 1),
            "avg_demand_during_lead_time": round(avg_daily_demand * lead_time_days, 1),
            "service_level": service_level,
            "combined_std_dev": round(combined_std_dev, 2),
            "recommendation": f"Reorder when inventory reaches {round(reorder_point, 1)} units"
        }


# Global instance
_optimizer: InventoryOptimizer | None = None


def get_inventory_optimizer() -> InventoryOptimizer:
    """Get or create global inventory optimizer."""
    global _optimizer
    if _optimizer is None:
        _optimizer = InventoryOptimizer()
    return _optimizer
