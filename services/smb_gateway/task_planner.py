"""
Task Planner Agent - GitHub Copilot-style task decomposition

Breaks down user queries into executable sub-tasks and runs them step-by-step.
Shows progress like: "✓ Schema discovered → ⚙️ Calculating metrics → ✓ Complete"
"""
import logging
import uuid
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class TaskStatus(Enum):
    """Task execution status"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    AWAITING_HUMAN = "awaiting_human"


@dataclass
class SubTask:
    """A single executable sub-task"""
    id: str
    description: str
    status: TaskStatus
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class TaskPlannerAgent:
    """
    Decomposes user queries into executable sub-tasks
    Like GitHub Copilot Workspace's task planning
    """
    def __init__(self) -> None:
        # Registry of task handlers for extensibility
        # key = task_id, value = callable accepting full data dict and returning result dict
        self._task_handlers: Dict[str, Callable[[Dict[str, List[Dict[str, Any]]]], Dict[str, Any]]] = {}
        # Human-in-the-loop review gates (task ids that require human approval)
        self._review_gates: set[str] = {"generate_report"}
        # Pending reviews storage: review_id -> context
        self._pending_reviews: Dict[str, Dict[str, Any]] = {}
        self._register_default_tasks()

    def register_task(
        self,
        task_id: str,
        handler: Callable[[Dict[str, List[Dict[str, Any]]]], Dict[str, Any]]
    ) -> None:
        """Register or override a task handler.

        Args:
            task_id: Identifier used in SubTask.id
            handler: Callable receiving the full data dict and returning a result dict
        """
        self._task_handlers[task_id] = handler

    def _register_default_tasks(self) -> None:
        """Register built-in task handlers. New tasks can be added at runtime via register_task."""
        self.register_task("discover_schema", lambda data: self._discover_schema(data))
        self.register_task("analyze_inventory_volume", lambda data: self._analyze_inventory_volume(data.get("inventory", [])))
        self.register_task("analyze_inventory_value", lambda data: self._analyze_inventory_value(data.get("inventory", [])))
        self.register_task("identify_top_products", lambda data: self._identify_top_products(data.get("inventory", [])))
        self.register_task("detect_stock_issues", lambda data: self._detect_stock_issues(data.get("inventory", [])))
        self.register_task("calculate_revenue", lambda data: self._calculate_revenue(data.get("orders", [])))
        self.register_task("analyze_order_trends", lambda data: self._analyze_order_trends(data.get("orders", [])))
        self.register_task("generate_report", lambda data: {"status": "ready"})
    
    def create_plan(self, user_query: str, available_data: Dict[str, int]) -> List[SubTask]:
        """
        Create execution plan from user query
        
        Args:
            user_query: Natural language query
            available_data: Dict of {data_type: record_count}
            
        Returns:
            List of SubTasks to execute
        """
        query_lower = user_query.lower()
        tasks = []
        
        # Always start with schema discovery
        tasks.append(SubTask(
            id="discover_schema",
            description="🔍 Discovering data structure",
            status=TaskStatus.PENDING
        ))
        
        # Determine analysis type
        if any(word in query_lower for word in ["inventory", "stock", "product"]):
            tasks.extend([
                SubTask(
                    id="analyze_inventory_volume",
                    description="📦 Analyzing inventory volume",
                    status=TaskStatus.PENDING
                ),
                SubTask(
                    id="analyze_inventory_value",
                    description="💰 Calculating inventory value",
                    status=TaskStatus.PENDING
                ),
                SubTask(
                    id="identify_top_products",
                    description="⭐ Identifying top products",
                    status=TaskStatus.PENDING
                ),
                SubTask(
                    id="detect_stock_issues",
                    description="⚠️ Detecting stock issues",
                    status=TaskStatus.PENDING
                )
            ])
        
        elif any(word in query_lower for word in ["revenue", "sales", "order"]):
            tasks.extend([
                SubTask(
                    id="calculate_revenue",
                    description="💵 Calculating revenue metrics",
                    status=TaskStatus.PENDING
                ),
                SubTask(
                    id="analyze_order_trends",
                    description="📈 Analyzing order trends",
                    status=TaskStatus.PENDING
                ),
                SubTask(
                    id="identify_top_customers",
                    description="👤 Identifying top customers",
                    status=TaskStatus.PENDING
                )
            ])
        
        elif any(word in query_lower for word in ["customer", "segment"]):
            tasks.extend([
                SubTask(
                    id="analyze_customer_base",
                    description="👥 Analyzing customer base",
                    status=TaskStatus.PENDING
                ),
                SubTask(
                    id="segment_customers",
                    description="🎯 Segmenting customers",
                    status=TaskStatus.PENDING
                )
            ])
        
        else:
            # General analysis
            tasks.extend([
                SubTask(
                    id="generate_overview",
                    description="📊 Generating business overview",
                    status=TaskStatus.PENDING
                ),
                SubTask(
                    id="identify_insights",
                    description="💡 Identifying key insights",
                    status=TaskStatus.PENDING
                )
            ])
        
        # Always end with report generation
        tasks.append(SubTask(
            id="generate_report",
            description="📝 Generating detailed report",
            status=TaskStatus.PENDING
        ))
        
        logger.info(f"[TaskPlanner] Created plan with {len(tasks)} tasks for: {user_query}")
        return tasks
    
    def execute_task(
        self, 
        task: SubTask, 
        data: Dict[str, List[Dict[str, Any]]]
    ) -> SubTask:
        """
        Execute a single sub-task
        
        Args:
            task: SubTask to execute
            data: Available data
            
        Returns:
            Updated SubTask with results
        """
        task.status = TaskStatus.IN_PROGRESS
        
        try:
            handler = self._task_handlers.get(task.id)
            if handler is not None:
                # Execute handler
                result = handler(data)

                # Human-in-the-loop gate
                if task.id in self._review_gates:
                    review_id = f"rev-{task.id}-{uuid.uuid4().hex[:8]}"
                    # Store pending review context
                    self._pending_reviews[review_id] = {
                        "task_id": task.id,
                        "description": task.description,
                        "proposed_result": result,
                    }
                    # Mark task as awaiting human approval
                    task.status = TaskStatus.AWAITING_HUMAN
                    task.result = {
                        "awaiting_human": True,
                        "review_id": review_id,
                        "proposed_result": result,
                        "message": "Awaiting human approval for this step",
                    }
                    logger.info(f"[TaskPlanner] ⏸ Task '{task.id}' awaiting human review (review_id={review_id})")
                    return task
                else:
                    task.result = result
            else:
                # Allow external systems to hook in new tasks later
                task.result = {"status": "not_implemented", "message": f"No handler registered for task '{task.id}'"}

            task.status = TaskStatus.COMPLETED
            logger.info(f"[TaskPlanner] ✓ Task completed: {task.id}")

        except Exception as e:
            task.status = TaskStatus.FAILED
            task.error = str(e)
            logger.error(f"[TaskPlanner] ✗ Task failed: {task.id} - {e}")
        
        return task

    # -----------------------------
    # Human-in-the-loop (HITL) APIs
    # -----------------------------
    def require_human_review_for(self, task_id: str) -> None:
        """Enable human review gate for a task id."""
        self._review_gates.add(task_id)

    def remove_human_review_for(self, task_id: str) -> None:
        """Disable human review gate for a task id."""
        self._review_gates.discard(task_id)

    def list_pending_reviews(self) -> List[Dict[str, Any]]:
        """Return a list of pending review contexts."""
        return [
            {"review_id": rid, **ctx}
            for rid, ctx in self._pending_reviews.items()
        ]

    def submit_human_review(
        self,
        review_id: str,
        approved: bool,
        feedback: Optional[str] = None,
        corrections: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Submit the result of a human review.

        Returns a summary dict suitable for attaching to task results or logs.
        Note: The orchestrator should update the corresponding SubTask's status
        based on this response if it still holds a reference to the SubTask.
        """
        ctx = self._pending_reviews.pop(review_id, None)
        if not ctx:
            return {
                "status": "error",
                "message": f"Unknown review_id: {review_id}",
            }

        final_result = ctx["proposed_result"]
        if corrections:
            # Shallow merge corrections on top of proposed result
            if isinstance(final_result, dict):
                final_result = {**final_result, **corrections}
            else:
                final_result = {"value": final_result, **corrections}

        review_summary = {
            "review_id": review_id,
            "task_id": ctx["task_id"],
            "approved": approved,
            "feedback": feedback,
            "final_result": final_result,
            "status": "approved" if approved else "revisions_requested",
        }

        logger.info(
            f"[TaskPlanner] 👤 Human review {'approved' if approved else 'requested revisions'} for {ctx['task_id']} (review_id={review_id})"
        )
        return review_summary

    # ---------------------------------
    # Optional: LangChain Tool Adapters
    # ---------------------------------
    def register_langchain_tool(
        self,
        task_id: str,
        tool: Any,
        input_builder: Optional[Callable[[Dict[str, List[Dict[str, Any]]]], Any]] = None,
        result_mapper: Optional[Callable[[Any], Dict[str, Any]]] = None,
    ) -> None:
        """Register a LangChain Tool as a task handler.

        Args:
            task_id: The SubTask.id to bind to this tool
            tool: A LangChain Tool-like object exposing invoke/run/call
            input_builder: Builds tool input from our data dict (defaults to passing full data)
            result_mapper: Maps tool output to a dict result (defaults to wrapping under {'tool_output': ...})
        """
        def _handler(data: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Any]:
            _input = input_builder(data) if input_builder else data
            # Try common call patterns
            if hasattr(tool, "invoke"):
                out = tool.invoke(_input)  # type: ignore[attr-defined]
            elif hasattr(tool, "run"):
                out = tool.run(_input)  # type: ignore[attr-defined]
            elif callable(tool):
                out = tool(_input)
            else:
                raise RuntimeError("Unsupported tool: missing invoke/run/callable")

            if result_mapper:
                return result_mapper(out)
            # Default mapping
            return {"tool_output": out}

        self.register_task(task_id, _handler)
    
    def _discover_schema(self, data: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Any]:
        """Discover data schemas with agent thinking and evidence"""
        schemas = {}
        agent_thoughts = []
        evidence = []
        
        for data_type, records in data.items():
            if records:
                sample = records[0]
                
                # Record agent thinking
                agent_thoughts.append({
                    "agent": "Schema Discovery Agent",
                    "thought": f"I need to understand the structure of {data_type} data to perform accurate analysis",
                    "action": f"Inspecting {len(records)} records to identify field names and data types",
                    "observation": f"Found {len(records):,} records with {len(sample.keys())} fields",
                    "data_source": data_type
                })
                
                # Record evidence
                evidence.append({
                    "claim": f"Analyzed {len(records):,} {data_type} records",
                    "data_source": data_type,
                    "calculation": "COUNT(records)",
                    "value": len(records),
                    "confidence": 1.0
                })
                
                schemas[data_type] = {
                    "record_count": len(records),
                    "fields": list(sample.keys()),
                    "sample": sample
                }
                
                # Log field discovery
                agent_thoughts.append({
                    "agent": "Schema Discovery Agent",
                    "thought": "I should identify the key fields available for analysis",
                    "action": f"Examining field names: {', '.join(list(sample.keys())[:5])}{'...' if len(sample.keys()) > 5 else ''}",
                    "observation": f"Identified {len(sample.keys())} fields that can be used for calculations",
                    "data_source": data_type
                })
        
        return {
            "schemas": schemas,
            "agent_thoughts": agent_thoughts,
            "evidence": evidence
        }
    
    def _analyze_inventory_volume(self, inventory: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze inventory volume using ANY field names with agent thinking"""
        if not inventory:
            return {"error": "No inventory data"}
        
        agent_thoughts = []
        evidence = []
        
        # Discover quantity field dynamically
        sample = inventory[0]
        qty_field = None
        for field in sample.keys():
            if any(term in field.lower() for term in ["quantity", "qty", "amount", "count"]):
                qty_field = field
                break
        
        if not qty_field:
            return {"error": "No quantity field found"}
        
        # Record discovery thinking
        agent_thoughts.append({
            "agent": "Volume Analysis Agent",
            "thought": "I need to calculate total inventory volume across all products",
            "action": f"Identified quantity field as '{qty_field}' and summing values from {len(inventory)} records",
            "observation": f"Using field '{qty_field}' to calculate volume metrics",
            "data_source": "inventory"
        })
        
        total_items = len(inventory)
        # Convert to float, handling strings and None
        quantities = []
        for item in inventory:
            val = item.get(qty_field, 0)
            try:
                quantities.append(abs(float(val)) if val else 0)
            except (ValueError, TypeError):
                quantities.append(0)
        
        total_quantity = sum(quantities)
        avg_quantity = total_quantity / total_items if total_items > 0 else 0
        
        # Record evidence
        evidence.append({
            "claim": f"Total unique products: {total_items:,}",
            "data_source": "inventory",
            "calculation": f"COUNT(DISTINCT records)",
            "value": total_items,
            "confidence": 1.0
        })
        
        evidence.append({
            "claim": f"Total quantity across all products: {total_quantity:,}",
            "data_source": "inventory",
            "calculation": f"SUM({qty_field})",
            "value": total_quantity,
            "confidence": 1.0
        })
        
        # Record final observation
        agent_thoughts.append({
            "agent": "Volume Analysis Agent",
            "thought": "Let me interpret what these volume numbers mean for the business",
            "action": f"Calculated average quantity per product: {avg_quantity:.2f}",
            "observation": f"Total volume is {total_quantity:,} units distributed across {total_items:,} products",
            "data_source": "inventory"
        })
        
        return {
            "total_items": total_items,
            "total_quantity": total_quantity,
            "average_quantity_per_item": round(avg_quantity, 2),
            "quantity_field_used": qty_field,
            "agent_thoughts": agent_thoughts,
            "evidence": evidence
        }
    
    def _analyze_inventory_value(self, inventory: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze inventory value using ANY field names with agent thinking"""
        if not inventory:
            return {"error": "No inventory data"}
        
        agent_thoughts = []
        evidence = []
        
        sample = inventory[0]
        
        # Discover price and quantity fields
        qty_field = None
        price_field = None
        
        for field in sample.keys():
            if any(term in field.lower() for term in ["quantity", "qty", "amount"]):
                qty_field = field
            if any(term in field.lower() for term in ["price", "cost", "value"]):
                price_field = field
        
        if not qty_field or not price_field:
            return {"error": f"Missing fields: qty={qty_field}, price={price_field}"}
        
        # Record discovery thinking
        agent_thoughts.append({
            "agent": "Value Analysis Agent",
            "thought": "To calculate total inventory value, I need to multiply quantity by unit price for each item",
            "action": f"Discovered quantity field '{qty_field}' and price field '{price_field}'",
            "observation": f"Will calculate value as {qty_field} × {price_field} for each product",
            "data_source": "inventory"
        })
        
        # Calculate total value with proper type conversion
        values = []
        for item in inventory:
            try:
                qty = float(item.get(qty_field, 0)) if item.get(qty_field) else 0
                price = float(item.get(price_field, 0)) if item.get(price_field) else 0
                values.append(abs(qty) * price)
            except (ValueError, TypeError):
                values.append(0)
        
        total_value = sum(values)
        
        # Record evidence
        evidence.append({
            "claim": f"Total inventory value: ${total_value:,.2f}",
            "data_source": "inventory",
            "calculation": f"SUM({qty_field} × {price_field})",
            "value": total_value,
            "confidence": 1.0
        })
        
        # Record final observation
        agent_thoughts.append({
            "agent": "Value Analysis Agent",
            "thought": "This total value represents the worth of all inventory currently on hand",
            "action": f"Calculated total value across {len(inventory)} items",
            "observation": f"Total inventory is worth ${total_value:,.2f}",
            "data_source": "inventory"
        })
        
        return {
            "total_value": round(total_value, 2),
            "fields_used": {
                "quantity": qty_field,
                "price": price_field
            },
            "agent_thoughts": agent_thoughts,
            "evidence": evidence
        }
    
    def _identify_top_products(self, inventory: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Identify top products by volume with agent thinking"""
        if not inventory:
            return {"error": "No inventory data"}
        
        from collections import defaultdict
        
        agent_thoughts = []
        evidence = []
        
        sample = inventory[0]
        
        # Find identifier and description fields
        id_field = None
        desc_field = None
        qty_field = None
        price_field = None
        
        for field in sample.keys():
            if any(term in field.lower() for term in ["code", "sku", "id"]) and not id_field:
                id_field = field
            if any(term in field.lower() for term in ["description", "name", "title"]) and not desc_field:
                desc_field = field
            if any(term in field.lower() for term in ["quantity", "qty"]) and not qty_field:
                qty_field = field
            if any(term in field.lower() for term in ["price", "cost"]) and not price_field:
                price_field = field
        
        if not id_field or not qty_field:
            return {"error": "Missing required fields"}
        
        # Record thinking
        agent_thoughts.append({
            "agent": "Product Analysis Agent",
            "thought": "I need to identify which products have the highest volume to help prioritize inventory management",
            "action": f"Grouping inventory by product {id_field} and summing {qty_field} for each",
            "observation": f"Will rank products by total volume to find top performers",
            "data_source": "inventory"
        })
        
        # Group by product
        products = defaultdict(lambda: {"quantity": 0.0, "description": "", "value": 0.0})
        
        for item in inventory:
            product_id = item.get(id_field)
            if product_id:
                try:
                    qty = float(item.get(qty_field, 0)) if item.get(qty_field) else 0.0
                    prod_data = products[product_id]
                    prod_data["quantity"] = float(prod_data["quantity"]) + abs(qty)
                    if desc_field:
                        prod_data["description"] = item.get(desc_field, product_id)
                    if price_field:
                        price = float(item.get(price_field, 0)) if item.get(price_field) else 0.0
                        prod_data["value"] = float(prod_data["value"]) + abs(qty) * price
                except (ValueError, TypeError):
                    continue
        
        # Sort by quantity
        top_products = sorted(
            [(k, v) for k, v in products.items()],
            key=lambda x: x[1]["quantity"],
            reverse=True
        )[:10]
        
        # Record evidence for top products
        for i, (prod_id, data) in enumerate(top_products[:5], 1):
            desc = str(data.get("description", ""))[:30]
            qty = data.get("quantity", 0)
            evidence.append({
                "claim": f"#{i} Product: {desc} - {qty:,} units",
                "data_source": "inventory",
                "calculation": f"GROUP BY {id_field}, SUM({qty_field})",
                "value": qty,
                "confidence": 1.0
            })
        
        # Record observation
        if top_products:
            top_qty = float(top_products[0][1].get("quantity", 0))
            total_top_10 = sum(float(p[1].get("quantity", 0)) for p in top_products)
            pct = (top_qty / total_top_10 * 100) if total_top_10 > 0 else 0
            
            agent_thoughts.append({
                "agent": "Product Analysis Agent",
                "thought": "These top products represent the highest volume items and should be prioritized",
                "action": f"Sorted {len(products)} unique products by volume",
                "observation": f"Top product has {int(top_qty):,} units, which is {pct:.1f}% of top 10",
                "data_source": "inventory"
            })
        
        return {
            "top_10_products": [
                {
                    "id": prod_id,
                    "description": data["description"],
                    "quantity": data["quantity"],
                    "value": round(float(data["value"]), 2) if isinstance(data["value"], (int, float)) else 0
                }
                for prod_id, data in top_products
            ],
            "agent_thoughts": agent_thoughts,
            "evidence": evidence
        }
    
    def _detect_stock_issues(self, inventory: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Detect low stock or out-of-stock items with agent thinking"""
        if not inventory:
            return {"error": "No inventory data"}
        
        agent_thoughts = []
        evidence = []
        
        sample = inventory[0]
        qty_field = None
        
        for field in sample.keys():
            if any(term in field.lower() for term in ["quantity", "qty", "stock"]):
                qty_field = field
                break
        
        if not qty_field:
            return {"error": "No quantity field found"}
        
        # Record thinking
        agent_thoughts.append({
            "agent": "Stock Health Agent",
            "thought": "I need to identify products that might need reordering or immediate attention",
            "action": f"Calculating average quantity from {qty_field} to set reorder thresholds",
            "observation": "Will flag items below 30% of average as low stock and items at zero as critical",
            "data_source": "inventory"
        })
        
        # Calculate average quantity with proper type conversion
        quantities = []
        for item in inventory:
            try:
                qty = float(item.get(qty_field, 0)) if item.get(qty_field) else 0
                quantities.append(abs(qty))
            except (ValueError, TypeError):
                quantities.append(0)
        
        total_qty = sum(quantities)
        avg_qty = total_qty / len(inventory) if inventory else 0
        
        # Items below 30% of average are "low stock"
        threshold = avg_qty * 0.3
        
        low_stock_items = []
        out_of_stock_items = []
        
        for i, item in enumerate(inventory):
            qty = quantities[i]
            if qty == 0:
                out_of_stock_items.append(item)
            elif qty < threshold:
                low_stock_items.append(item)
        
        # Record evidence
        evidence.append({
            "claim": f"{len(low_stock_items):,} items below reorder threshold",
            "data_source": "inventory",
            "calculation": f"COUNT WHERE {qty_field} < {threshold:.2f}",
            "value": len(low_stock_items),
            "confidence": 0.9
        })
        
        evidence.append({
            "claim": f"{len(out_of_stock_items):,} items completely out of stock",
            "data_source": "inventory",
            "calculation": f"COUNT WHERE {qty_field} = 0",
            "value": len(out_of_stock_items),
            "confidence": 1.0
        })
        
        # Record observation
        total_issues = len(low_stock_items) + len(out_of_stock_items)
        pct_issues = (total_issues / len(inventory) * 100) if inventory else 0
        
        agent_thoughts.append({
            "agent": "Stock Health Agent",
            "thought": "These items need immediate attention to prevent stockouts and lost sales",
            "action": f"Identified {total_issues} items needing attention out of {len(inventory)} total",
            "observation": f"{pct_issues:.1f}% of inventory needs reordering - {len(out_of_stock_items)} are critical (out of stock)",
            "data_source": "inventory"
        })
        
        return {
            "low_stock_count": len(low_stock_items),
            "out_of_stock_count": len(out_of_stock_items),
            "threshold_quantity": round(threshold, 2),
            "items_needing_attention": total_issues,
            "agent_thoughts": agent_thoughts,
            "evidence": evidence
        }
    
    def _calculate_revenue(self, orders: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate revenue metrics with agent thinking"""
        if not orders:
            return {"error": "No order data"}
        
        agent_thoughts = []
        evidence = []
        
        sample = orders[0]
        amount_field = None
        
        for field in sample.keys():
            if any(term in field.lower() for term in ["amount", "total", "value", "revenue"]):
                amount_field = field
                break
        
        if not amount_field:
            return {"error": "No amount field found"}
        
        # Record thinking
        agent_thoughts.append({
            "agent": "Revenue Analysis Agent",
            "thought": "I need to calculate total revenue and understand order patterns",
            "action": f"Summing {amount_field} field from {len(orders)} orders",
            "observation": f"Will calculate total revenue and average order value",
            "data_source": "orders"
        })
        
        total_revenue = sum(float(order.get(amount_field, 0)) for order in orders)
        avg_order_value = total_revenue / len(orders) if orders else 0
        
        # Record evidence
        evidence.append({
            "claim": f"Total revenue: ${total_revenue:,.2f}",
            "data_source": "orders",
            "calculation": f"SUM({amount_field})",
            "value": total_revenue,
            "confidence": 1.0
        })
        
        evidence.append({
            "claim": f"Average order value: ${avg_order_value:,.2f}",
            "data_source": "orders",
            "calculation": f"AVG({amount_field})",
            "value": avg_order_value,
            "confidence": 1.0
        })
        
        # Record observation
        agent_thoughts.append({
            "agent": "Revenue Analysis Agent",
            "thought": "This revenue represents business performance across all orders",
            "action": f"Processed {len(orders)} orders totaling ${total_revenue:,.2f}",
            "observation": f"Average order is ${avg_order_value:,.2f} per transaction",
            "data_source": "orders"
        })
        
        return {
            "total_revenue": round(total_revenue, 2),
            "order_count": len(orders),
            "average_order_value": round(avg_order_value, 2),
            "agent_thoughts": agent_thoughts,
            "evidence": evidence
        }
    
    def _analyze_order_trends(self, orders: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze order trends over time"""
        if not orders:
            return {"error": "No order data"}
        
        from collections import defaultdict
        
        sample = orders[0]
        date_field = None
        
        for field in sample.keys():
            if any(term in field.lower() for term in ["date", "time", "timestamp"]):
                date_field = field
                break
        
        if not date_field:
            return {"error": "No date field found"}
        
        # Group by period (month)
        trends = defaultdict(int)
        
        for order in orders:
            date_str = str(order.get(date_field, ""))
            if len(date_str) >= 7:
                period = date_str[:7]  # YYYY-MM
                trends[period] += 1
        
        sorted_trends = sorted(trends.items())
        
        return {
            "periods_analyzed": len(sorted_trends),
            "trend_data": dict(sorted_trends),
            "date_field_used": date_field
        }


# Global instance
_task_planner: Optional[TaskPlannerAgent] = None


def get_task_planner() -> TaskPlannerAgent:
    """Get task planner singleton"""
    global _task_planner
    if _task_planner is None:
        _task_planner = TaskPlannerAgent()
    return _task_planner
