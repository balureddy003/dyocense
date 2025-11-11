"""
CycloneRake Seed Data
Generate realistic business data for CycloneRake.com (outdoor equipment retailer)
"""
from datetime import datetime, timedelta
import random

def generate_cyclonerake_data():
    """Generate realistic CycloneRake business data"""
    now = datetime.now()
    
    # CycloneRake product categories
    products = {
        "Rakes & Lawn Tools": [
            {"name": "CycloneRake PRO", "price": 299.99, "cost": 150.00, "popularity": 0.3},
            {"name": "CycloneRake LITE", "price": 199.99, "cost": 100.00, "popularity": 0.25},
            {"name": "Replacement Tines (Set of 12)", "price": 49.99, "cost": 15.00, "popularity": 0.15},
            {"name": "Extension Handle", "price": 39.99, "cost": 12.00, "popularity": 0.1},
            {"name": "Storage Bag", "price": 29.99, "cost": 8.00, "popularity": 0.08},
        ],
        "Lawn Care Equipment": [
            {"name": "Leaf Blower Attachment", "price": 89.99, "cost": 35.00, "popularity": 0.05},
            {"name": "Garden Cart", "price": 149.99, "cost": 60.00, "popularity": 0.04},
            {"name": "Yard Waste Bags (Pack of 10)", "price": 24.99, "cost": 8.00, "popularity": 0.03},
        ]
    }
    
    # Generate orders for last 90 days (seasonal: peak in fall)
    orders = []
    order_id = 1
    
    for days_ago in range(90):
        date = now - timedelta(days=days_ago)
        month = date.month
        
        # Seasonal pattern: Sep-Nov is peak season (leaf raking)
        if month in [9, 10, 11]:  # Fall
            daily_orders = random.randint(15, 25)
        elif month in [3, 4, 5]:  # Spring
            daily_orders = random.randint(8, 15)
        else:  # Winter/Summer
            daily_orders = random.randint(3, 8)
        
        for _ in range(daily_orders):
            # Pick products for this order
            category = random.choice(list(products.keys()))
            num_items = random.choices([1, 2, 3], weights=[0.7, 0.25, 0.05])[0]
            items = random.sample(products[category], min(num_items, len(products[category])))
            
            total_amount = sum(item["price"] for item in items)
            total_cost = sum(item["cost"] for item in items)
            
            orders.append({
                "id": f"ORD-CR-{date.strftime('%Y%m%d')}-{order_id:04d}",
                "customer_id": f"cust-cr-{random.randint(1, 500)}",
                "total_amount": round(total_amount, 2),
                "total_cost": round(total_cost, 2),
                "profit": round(total_amount - total_cost, 2),
                "status": "completed" if days_ago > 2 else "pending",
                "items_count": len(items),
                "created_at": date.isoformat(),
                "product_category": category,
                "products": [item["name"] for item in items],
                "source": "website",
                "shipping_state": random.choice(["CA", "TX", "FL", "NY", "IL", "PA", "OH", "GA", "NC", "MI"]),
            })
            order_id += 1
    
    # Generate inventory based on products
    inventory = []
    inv_id = 1
    
    for category, items in products.items():
        for product in items:
            # Stock levels based on popularity
            if product["popularity"] > 0.2:  # High demand
                quantity = random.randint(50, 150)
                status = "in_stock"
            elif product["popularity"] > 0.1:  # Medium demand
                quantity = random.randint(20, 50)
                status = "in_stock" if quantity > 10 else "low_stock"
            else:  # Low demand
                quantity = random.randint(5, 25)
                status = "in_stock" if quantity > 10 else "low_stock"
            
            inventory.append({
                "id": f"inv-cr-{inv_id}",
                "sku": f"CR-SKU-{inv_id:04d}",
                "product_name": product["name"],
                "category": category,
                "quantity": quantity,
                "reorder_point": 15,
                "unit_cost": product["cost"],
                "retail_price": product["price"],
                "status": status,
                "supplier": "CycloneRake Manufacturing",
                "last_restock": (now - timedelta(days=random.randint(5, 30))).isoformat(),
            })
            inv_id += 1
    
    # Generate customer base
    customers = []
    
    # Customer segments for lawn care business
    for i in range(500):
        if i < 50:  # VIP customers (10%) - contractors, landscapers
            total_orders = random.randint(8, 25)
            lifetime_value = random.randint(1500, 5000)
            segment = "vip_contractor"
        elif i < 200:  # Regular homeowners (30%)
            total_orders = random.randint(2, 7)
            lifetime_value = random.randint(300, 1200)
            segment = "regular_homeowner"
        else:  # One-time buyers (60%)
            total_orders = 1
            lifetime_value = random.randint(150, 400)
            segment = "one_time"
        
        customers.append({
            "id": f"cust-cr-{i+1}",
            "name": f"Customer {i+1}",
            "email": f"customer{i+1}@example.com",
            "total_orders": total_orders,
            "lifetime_value": round(lifetime_value, 2),
            "segment": segment,
            "last_order_date": (now - timedelta(days=random.randint(1, 90))).isoformat(),
            "created_at": (now - timedelta(days=random.randint(90, 730))).isoformat(),
            "state": random.choice(["CA", "TX", "FL", "NY", "IL", "PA", "OH", "GA", "NC", "MI"]),
        })
    
    return {
        "orders": orders,
        "inventory": inventory,
        "customers": customers,
        "_meta": {
            "generated": now.isoformat(),
            "business_name": "CycloneRake",
            "industry": "outdoor_equipment",
            "website": "https://cyclonerake.com",
            "data_source": "seeded",
            "note": "Realistic business data for CycloneRake outdoor equipment retailer"
        }
    }


# Export for direct usage
if __name__ == "__main__":
    import json
    data = generate_cyclonerake_data()
    print(json.dumps({
        "orders_count": len(data["orders"]),
        "inventory_count": len(data["inventory"]),
        "customers_count": len(data["customers"]),
        "total_revenue": sum(o["total_amount"] for o in data["orders"]),
        "total_profit": sum(o["profit"] for o in data["orders"]),
    }, indent=2))
