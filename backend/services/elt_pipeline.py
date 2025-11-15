"""
ELT Pipeline Service
Transforms raw_connector_data into structured business_metrics
"""
import json
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional
import uuid


class ELTPipeline:
    """Extract, Load, Transform pipeline for connector data"""
    
    def __init__(self, backend):
        """Initialize with PostgreSQL backend"""
        self.backend = backend
    
    async def process_inventory_data(self, tenant_id: str, source_id: str) -> Dict[str, Any]:
        """
        Transform raw inventory CSV into business metrics
        
        Returns:
            - total_inventory_value
            - product_count
            - stockout_risk items
            - overstock items
        """
        with self.backend.get_connection() as conn:
            with conn.cursor() as cur:
                # Get raw data
                cur.execute(
                    """
                    SELECT data FROM raw_connector_data 
                    WHERE tenant_id = %s AND source_id = %s 
                    ORDER BY ingested_at DESC LIMIT 1
                    """,
                    [tenant_id, source_id]
                )
                row = cur.fetchone()
                if not row:
                    return {"error": "No data found"}
                
                raw_data = row[0]
                sample_rows = raw_data.get('sample_rows', [])
                
                # Calculate metrics
                total_value = 0.0
                stockout_risk = []
                overstock = []
                products = []
                
                for item in sample_rows:
                    sku = item.get('sku', '')
                    current_stock = float(item.get('current_stock', 0))
                    min_stock = float(item.get('min_stock', 0))
                    max_stock = float(item.get('max_stock', 0))
                    unit_cost = float(item.get('unit_cost', 0))
                    
                    item_value = current_stock * unit_cost
                    total_value += item_value
                    
                    # Check stockout risk
                    if current_stock <= min_stock * 1.1:  # Within 10% of min
                        stockout_risk.append({
                            'sku': sku,
                            'current_stock': current_stock,
                            'min_stock': min_stock,
                            'shortfall': min_stock - current_stock
                        })
                    
                    # Check overstock
                    if current_stock >= max_stock * 0.9:  # Within 10% of max
                        overstock.append({
                            'sku': sku,
                            'current_stock': current_stock,
                            'max_stock': max_stock,
                            'excess': current_stock - max_stock
                        })
                    
                    products.append({
                        'sku': sku,
                        'product_name': item.get('product_name', ''),
                        'current_stock': current_stock,
                        'inventory_value': item_value,
                        'unit_cost': unit_cost,
                        'location': item.get('location', '')
                    })
                
                # Store in business_metrics table
                metric_id = str(uuid.uuid4())
                cur.execute(
                    """
                    INSERT INTO business_metrics 
                    (metric_id, tenant_id, metric_name, value, metric_type, 
                     timestamp, extra_data)
                    VALUES (%s, %s, %s, %s, %s, NOW(), %s)
                    """,
                    [
                        metric_id,
                        tenant_id,
                        'total_inventory_value',
                        total_value,
                        'inventory',
                        json.dumps({
                            'product_count': len(products),
                            'stockout_risk_count': len(stockout_risk),
                            'overstock_count': len(overstock),
                            'source_id': source_id
                        })
                    ]
                )
                conn.commit()
                
                return {
                    'total_inventory_value': round(total_value, 2),
                    'product_count': len(products),
                    'stockout_risk': stockout_risk,
                    'overstock': overstock,
                    'products': products,
                    'metric_id': metric_id
                }
    
    async def process_demand_data(self, tenant_id: str, source_id: str) -> Dict[str, Any]:
        """
        Transform raw demand CSV into time-series metrics
        
        Returns:
            - demand_by_sku
            - total_demand
            - growth_trends
        """
        with self.backend.get_connection() as conn:
            with conn.cursor() as cur:
                # Get raw data
                cur.execute(
                    """
                    SELECT data FROM raw_connector_data 
                    WHERE tenant_id = %s AND source_id = %s 
                    ORDER BY ingested_at DESC LIMIT 1
                    """,
                    [tenant_id, source_id]
                )
                row = cur.fetchone()
                if not row:
                    return {"error": "No data found"}
                
                raw_data = row[0]
                sample_rows = raw_data.get('sample_rows', [])
                
                # Aggregate demand by SKU
                demand_by_sku = {}
                for item in sample_rows:
                    sku = item.get('sku', '')
                    week = int(item.get('week', 0))
                    quantity = float(item.get('quantity', 0))
                    
                    if sku not in demand_by_sku:
                        demand_by_sku[sku] = []
                    
                    demand_by_sku[sku].append({
                        'week': week,
                        'quantity': quantity
                    })
                
                # Calculate trends
                trends = {}
                for sku, data in demand_by_sku.items():
                    sorted_data = sorted(data, key=lambda x: x['week'])
                    if len(sorted_data) >= 2:
                        first_qty = sorted_data[0]['quantity']
                        last_qty = sorted_data[-1]['quantity']
                        growth_rate = ((last_qty - first_qty) / first_qty * 100) if first_qty > 0 else 0
                        trends[sku] = {
                            'growth_rate_pct': round(growth_rate, 2),
                            'direction': 'up' if growth_rate > 0 else 'down',
                            'weeks_tracked': len(sorted_data)
                        }
                
                # Store total demand metric
                total_demand = sum(item['quantity'] for items in demand_by_sku.values() for item in items)
                metric_id = str(uuid.uuid4())
                cur.execute(
                    """
                    INSERT INTO business_metrics 
                    (metric_id, tenant_id, metric_name, value, metric_type, 
                     timestamp, extra_data)
                    VALUES (%s, %s, %s, %s, %s, NOW(), %s)
                    """,
                    [
                        metric_id,
                        tenant_id,
                        'total_demand',
                        total_demand,
                        'demand',
                        json.dumps({
                            'sku_count': len(demand_by_sku),
                            'trends': trends,
                            'source_id': source_id
                        })
                    ]
                )
                conn.commit()
                
                return {
                    'total_demand': round(total_demand, 2),
                    'demand_by_sku': demand_by_sku,
                    'trends': trends,
                    'metric_id': metric_id
                }
    
    async def run_full_pipeline(self, tenant_id: str) -> Dict[str, Any]:
        """
        Run complete ELT pipeline for all connectors
        
        Returns summary of all processed metrics
        """
        results = {
            'inventory': None,
            'demand': None,
            'processed_at': datetime.now(timezone.utc).isoformat()
        }
        
        with self.backend.get_connection() as conn:
            with conn.cursor() as cur:
                # Find all active connectors
                cur.execute(
                    """
                    SELECT source_id, connector_type FROM data_sources 
                    WHERE tenant_id = %s AND status = 'active'
                    """,
                    [tenant_id]
                )
                connectors = cur.fetchall()
                
                for source_id, connector_type in connectors:
                    if connector_type == 'csv_upload':
                        # Determine if inventory or demand based on columns
                        cur.execute(
                            """
                            SELECT data->'headers' as headers FROM raw_connector_data 
                            WHERE source_id = %s ORDER BY ingested_at DESC LIMIT 1
                            """,
                            [source_id]
                        )
                        header_row = cur.fetchone()
                        if header_row:
                            headers = header_row[0]
                            
                            # Check if it's inventory data
                            if 'current_stock' in str(headers):
                                results['inventory'] = await self.process_inventory_data(tenant_id, source_id)
                            
                            # Check if it's demand data
                            elif 'quantity' in str(headers) and 'week' in str(headers):
                                results['demand'] = await self.process_demand_data(tenant_id, source_id)
        
        return results
