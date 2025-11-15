"""
Narrative Generation Service
Synthesizes forecasts, optimizations, and metrics into natural language insights
Production version should use LangGraph multi-agent orchestration with LLMs
"""
from typing import Dict, List, Any, Optional
import json
from datetime import datetime, timezone


class NarrativeGenerator:
    """Simple narrative generation service"""
    
    def __init__(self, backend):
        """Initialize with PostgreSQL backend"""
        self.backend = backend
    
    def _format_currency(self, value: float) -> str:
        """Format value as currency"""
        return f"${value:,.2f}"
    
    def _format_percentage(self, value: float) -> str:
        """Format value as percentage"""
        return f"{value:.1f}%"
    
    def _generate_inventory_narrative(self, metrics: Dict[str, Any]) -> str:
        """Generate narrative from inventory metrics"""
        total_value = metrics.get('total_inventory_value', 0)
        product_count = metrics.get('product_count', 0)
        stockout_risk = metrics.get('stockout_risk', [])
        overstock = metrics.get('overstock', [])
        
        narrative = f"Your inventory consists of {product_count} products valued at {self._format_currency(total_value)}. "
        
        if stockout_risk:
            sku_list = ', '.join([item['sku'] for item in stockout_risk[:3]])
            narrative += f"⚠️ {len(stockout_risk)} items are at risk of stockout ({sku_list}). "
        
        if overstock:
            sku_list = ', '.join([item['sku'] for item in overstock[:3]])
            narrative += f"📦 {len(overstock)} items are overstocked ({sku_list}). "
        
        if not stockout_risk and not overstock:
            narrative += "✅ All inventory levels are within optimal ranges. "
        
        return narrative
    
    def _generate_forecast_narrative(self, forecast_data: Dict[str, Any]) -> str:
        """Generate narrative from forecast data"""
        forecasts = forecast_data.get('forecasts', {})
        periods = forecast_data.get('periods', 4)
        
        if not forecasts:
            return "No forecast data available. "
        
        narrative = f"Demand forecast for the next {periods} periods shows: "
        
        # Analyze trends
        growing_skus = []
        declining_skus = []
        
        for sku, data in forecasts.items():
            trend = data.get('trend', 0)
            if trend > 0.5:
                growing_skus.append(sku)
            elif trend < -0.5:
                declining_skus.append(sku)
        
        if growing_skus:
            narrative += f"📈 Growing demand for {', '.join(growing_skus[:3])}. "
        
        if declining_skus:
            narrative += f"📉 Declining demand for {', '.join(declining_skus[:3])}. "
        
        if not growing_skus and not declining_skus:
            narrative += "Stable demand expected across all products. "
        
        return narrative
    
    def _generate_optimization_narrative(self, opt_data: Dict[str, Any]) -> str:
        """Generate narrative from optimization results"""
        recommendations = opt_data.get('recommendations', [])
        total_savings = opt_data.get('total_potential_savings', 0)
        actions_required = opt_data.get('actions_required', 0)
        
        if not recommendations:
            return "No optimization recommendations available. "
        
        narrative = f"💡 Optimization analysis found {actions_required} actions to save {self._format_currency(total_savings)}. "
        
        # Count action types
        order_now = [r for r in recommendations if r['action'] == 'ORDER_NOW']
        reduce_stock = [r for r in recommendations if r['action'] == 'REDUCE_STOCK']
        
        if order_now:
            sku_list = ', '.join([r['sku'] for r in order_now[:3]])
            narrative += f"🔔 Reorder needed for {len(order_now)} items ({sku_list}). "
        
        if reduce_stock:
            sku_list = ', '.join([r['sku'] for r in reduce_stock[:3]])
            total_reduction_savings = sum(r['potential_saving'] for r in reduce_stock)
            narrative += f"💰 Reduce stock on {len(reduce_stock)} items to save {self._format_currency(total_reduction_savings)} ({sku_list}). "
        
        return narrative
    
    async def generate_narrative(
        self,
        tenant_id: str,
        question: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generate narrative answer to a business question
        
        Args:
            tenant_id: Tenant identifier
            question: Business question (e.g., "How can I reduce costs?")
            context: Optional context data
        
        Returns:
            Narrative response with supporting data
        """
        question_lower = question.lower()
        
        # Determine intent from question
        intent = None
        if any(word in question_lower for word in ['cost', 'save', 'reduce', 'optimize']):
            intent = 'cost_reduction'
        elif any(word in question_lower for word in ['forecast', 'demand', 'predict', 'future']):
            intent = 'demand_forecast'
        elif any(word in question_lower for word in ['inventory', 'stock', 'level']):
            intent = 'inventory_status'
        else:
            intent = 'general_overview'
        
        with self.backend.get_connection() as conn:
            with conn.cursor() as cur:
                narrative_parts = []
                supporting_data = {}
                
                # Get latest metrics
                if intent in ['inventory_status', 'general_overview', 'cost_reduction']:
                    cur.execute(
                        """
                        SELECT value, extra_data FROM business_metrics 
                        WHERE tenant_id = %s AND metric_name = 'total_inventory_value'
                        ORDER BY timestamp DESC LIMIT 1
                        """,
                        [tenant_id]
                    )
                    metric_row = cur.fetchone()
                    if metric_row:
                        inventory_data = {
                            'total_inventory_value': metric_row[0],
                            'product_count': metric_row[1].get('product_count', 0),
                            'stockout_risk_count': metric_row[1].get('stockout_risk_count', 0),
                            'overstock_count': metric_row[1].get('overstock_count', 0)
                        }
                        narrative_parts.append(self._generate_inventory_narrative(inventory_data))
                        supporting_data['inventory_metrics'] = inventory_data
                
                # Get latest forecast
                if intent in ['demand_forecast', 'general_overview']:
                    cur.execute(
                        """
                        SELECT predictions, horizon_days, model_type 
                        FROM forecasts 
                        WHERE tenant_id = %s AND metric_name = 'demand'
                        ORDER BY created_at DESC LIMIT 1
                        """,
                        [tenant_id]
                    )
                    forecast_row = cur.fetchone()
                    if forecast_row:
                        forecast_data = {
                            'forecasts': forecast_row[0],
                            'periods': forecast_row[1] // 7,  # Convert days to weeks
                            'model': forecast_row[2]
                        }
                        narrative_parts.append(self._generate_forecast_narrative(forecast_data))
                        supporting_data['forecast'] = forecast_data
                
                # Get latest optimization
                if intent in ['cost_reduction', 'general_overview']:
                    cur.execute(
                        """
                        SELECT solution, objective_value 
                        FROM optimization_runs 
                        WHERE tenant_id = %s AND problem_type = 'inventory_optimization'
                        ORDER BY created_at DESC LIMIT 1
                        """,
                        [tenant_id]
                    )
                    opt_row = cur.fetchone()
                    if opt_row:
                        recommendations = opt_row[0]
                        opt_data = {
                            'recommendations': recommendations,
                            'total_potential_savings': opt_row[1],
                            'actions_required': sum(1 for r in recommendations if r['action'] in ['ORDER_NOW', 'REDUCE_STOCK'])
                        }
                        narrative_parts.append(self._generate_optimization_narrative(opt_data))
                        supporting_data['optimization'] = opt_data
                
                # Combine narratives
                if not narrative_parts:
                    full_narrative = "No data available yet. Please run the ELT pipeline and generate forecasts/optimizations first."
                else:
                    full_narrative = ' '.join(narrative_parts)
                
                # Add specific recommendations based on intent
                recommendations = []
                if intent == 'cost_reduction' and 'optimization' in supporting_data:
                    opt = supporting_data['optimization']
                    for rec in opt['recommendations'][:5]:
                        if rec['action'] in ['ORDER_NOW', 'REDUCE_STOCK']:
                            recommendations.append({
                                'action': rec['action'],
                                'sku': rec['sku'],
                                'description': f"{rec['action'].replace('_', ' ').title()}: {rec['sku']} (Save {self._format_currency(rec['potential_saving'])})",
                                'potential_saving': rec['potential_saving']
                            })
                
                return {
                    'narrative': full_narrative,
                    'intent': intent,
                    'question': question,
                    'recommendations': recommendations,
                    'supporting_data': supporting_data,
                    'generated_at': datetime.now(timezone.utc).isoformat()
                }
