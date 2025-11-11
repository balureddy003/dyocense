"""
ERPNext Connector Test Script

Tests the ERPNext connector with real or mock ERPNext instance.
Run this to verify the connector is working correctly.

Usage:
    python test_erpnext_connector.py --url https://demo.erpnext.com --key YOUR_KEY --secret YOUR_SECRET
    python test_erpnext_connector.py --mock  # Use mock data
"""

import asyncio
import argparse
import sys
from datetime import datetime

# Add parent directory to path to import connector
sys.path.insert(0, '../..')

from services.connectors.erpnext import ERPNextConfig, ERPNextConnector, sync_erpnext_data


async def test_connection(config: ERPNextConfig) -> bool:
    """Test ERPNext API connection"""
    print("\n🔍 Testing ERPNext connection...")
    print(f"   URL: {config.api_url}")
    
    try:
        async with ERPNextConnector(config) as connector:
            success = await connector.test_connection()
            
            if success:
                print("✅ Connection successful!")
                return True
            else:
                print("❌ Connection failed - check credentials")
                return False
                
    except Exception as e:
        print(f"❌ Connection error: {e}")
        return False


async def test_inventory_sync(config: ERPNextConfig):
    """Test inventory data synchronization"""
    print("\n📦 Testing inventory sync...")
    
    try:
        async with ERPNextConnector(config) as connector:
            inventory = await connector.fetch_inventory()
            
            print(f"✅ Fetched {len(inventory)} inventory items")
            
            if inventory:
                print("\n📊 Sample inventory item:")
                item = inventory[0]
                print(f"   Item Code: {item.get('item_code')}")
                print(f"   Item Name: {item.get('item_name')}")
                print(f"   Stock Qty: {item.get('stock_qty')}")
                print(f"   Reorder Level: {item.get('reorder_level')}")
                print(f"   Needs Reorder: {item.get('needs_reorder')}")
                
                # Count items needing reorder
                reorder_count = sum(1 for item in inventory if item.get('needs_reorder'))
                print(f"\n⚠️  {reorder_count} items need reordering")
                
            return inventory
            
    except Exception as e:
        print(f"❌ Inventory sync error: {e}")
        return []


async def test_orders_sync(config: ERPNextConfig):
    """Test sales orders synchronization"""
    print("\n🛒 Testing sales orders sync...")
    
    try:
        async with ERPNextConnector(config) as connector:
            orders = await connector.fetch_orders()
            
            print(f"✅ Fetched {len(orders)} sales orders (last {config.lookback_days} days)")
            
            if orders:
                print("\n📊 Sample order:")
                order = orders[0]
                print(f"   Order ID: {order.get('order_id')}")
                print(f"   Customer: {order.get('customer_name')}")
                print(f"   Amount: {order.get('currency')} {order.get('total_amount'):.2f}")
                print(f"   Status: {order.get('status')}")
                print(f"   Date: {order.get('order_date')}")
                
                # Calculate totals
                total_revenue = sum(order.get('total_amount', 0) for order in orders)
                pending_orders = sum(1 for order in orders if order.get('is_pending'))
                
                print(f"\n💰 Total Revenue: {orders[0].get('currency', 'INR')} {total_revenue:,.2f}")
                print(f"⏳ Pending Orders: {pending_orders}")
                
            return orders
            
    except Exception as e:
        print(f"❌ Orders sync error: {e}")
        return []


async def test_suppliers_sync(config: ERPNextConfig):
    """Test suppliers synchronization"""
    print("\n🏭 Testing suppliers sync...")
    
    try:
        async with ERPNextConnector(config) as connector:
            suppliers = await connector.fetch_suppliers()
            
            print(f"✅ Fetched {len(suppliers)} suppliers")
            
            if suppliers:
                print("\n📊 Sample supplier:")
                supplier = suppliers[0]
                print(f"   Name: {supplier.get('supplier_name')}")
                print(f"   Group: {supplier.get('supplier_group')}")
                print(f"   Country: {supplier.get('country')}")
                print(f"   Payment Terms: {supplier.get('payment_terms')}")
                print(f"   Active: {supplier.get('is_active')}")
                
                # Count by country
                countries = {}
                for supplier in suppliers:
                    country = supplier.get('country', 'Unknown')
                    countries[country] = countries.get(country, 0) + 1
                
                print(f"\n🌍 Suppliers by country:")
                for country, count in sorted(countries.items(), key=lambda x: x[1], reverse=True)[:5]:
                    print(f"   {country}: {count}")
                
            return suppliers
            
    except Exception as e:
        print(f"❌ Suppliers sync error: {e}")
        return []


async def test_full_sync(config: ERPNextConfig):
    """Test complete data synchronization"""
    print("\n🔄 Testing full sync...")
    print(f"   Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    start = datetime.now()
    
    try:
        data = await sync_erpnext_data(config)
        
        duration = (datetime.now() - start).total_seconds()
        
        print(f"\n✅ Full sync completed in {duration:.2f} seconds")
        print(f"\n📊 Sync Summary:")
        print(f"   Inventory Items: {data.sync_metadata.get('inventory_count', 0)}")
        print(f"   Sales Orders: {data.sync_metadata.get('orders_count', 0)}")
        print(f"   Suppliers: {data.sync_metadata.get('suppliers_count', 0)}")
        print(f"   Synced At: {data.sync_metadata.get('synced_at')}")
        
        return data
        
    except Exception as e:
        print(f"❌ Full sync error: {e}")
        return None


async def run_tests(config: ERPNextConfig, test_type: str = 'all'):
    """Run connector tests"""
    print("=" * 60)
    print("ERPNext Connector Test Suite")
    print("=" * 60)
    
    # Test connection first
    connection_ok = await test_connection(config)
    
    if not connection_ok:
        print("\n⚠️  Cannot proceed - connection test failed")
        return
    
    # Run specific or all tests
    if test_type == 'all' or test_type == 'inventory':
        await test_inventory_sync(config)
    
    if test_type == 'all' or test_type == 'orders':
        await test_orders_sync(config)
    
    if test_type == 'all' or test_type == 'suppliers':
        await test_suppliers_sync(config)
    
    if test_type == 'all' or test_type == 'full':
        await test_full_sync(config)
    
    print("\n" + "=" * 60)
    print("✅ Test suite completed")
    print("=" * 60)


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Test ERPNext connector')
    parser.add_argument('--url', help='ERPNext URL (e.g., https://erp.example.com)')
    parser.add_argument('--key', help='API Key')
    parser.add_argument('--secret', help='API Secret')
    parser.add_argument('--lookback-days', type=int, default=90, help='Days to look back for orders')
    parser.add_argument('--test', choices=['all', 'connection', 'inventory', 'orders', 'suppliers', 'full'],
                        default='all', help='Which test to run')
    parser.add_argument('--mock', action='store_true', help='Use mock ERPNext instance (demo)')
    
    args = parser.parse_args()
    
    # Use demo instance if --mock specified
    if args.mock:
        print("⚠️  Using demo ERPNext instance")
        print("   Note: Demo instance may have rate limits or restrictions")
        config = ERPNextConfig(
            api_url="https://demo.erpnext.com",
            api_key="demo_api_key",
            api_secret="demo_api_secret",
            lookback_days=args.lookback_days
        )
    elif args.url and args.key and args.secret:
        config = ERPNextConfig(
            api_url=args.url,
            api_key=args.key,
            api_secret=args.secret,
            lookback_days=args.lookback_days
        )
    else:
        print("❌ Error: Provide --url, --key, --secret OR use --mock")
        parser.print_help()
        sys.exit(1)
    
    # Run tests
    asyncio.run(run_tests(config, args.test))


if __name__ == '__main__':
    main()
