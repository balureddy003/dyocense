#!/usr/bin/env python3
"""
Direct ingestion test to verify CSV data persists to connector_data table.
This bypasses the UI and HTTP layer to isolate database/ingestion issues.
"""
import logging
import sys
from pathlib import Path

# Add packages to path
sys.path.insert(0, str(Path(__file__).parent.parent / "packages"))
sys.path.insert(0, str(Path(__file__).parent.parent / "services" / "connectors"))

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_direct_ingestion():
    """Test ingestion by calling data_store_pg directly"""
    from connectors.data_store_pg import get_store
    
    # Test data
    tenant_id = "cyclonerake-97759e"
    connector_id = "test-csv-connector"
    data_type = "inventory"
    
    sample_data = [
        {"sku": "ITEM001", "stock": "100", "location": "WH-A"},
        {"sku": "ITEM002", "stock": "50", "location": "WH-B"},
        {"sku": "ITEM003", "stock": "75", "location": "WH-A"},
    ]
    
    metadata = {"source": "test_script", "test": True}
    
    logger.info(f"Testing ingestion for tenant={tenant_id}, connector={connector_id}")
    logger.info(f"Data: {len(sample_data)} records of type {data_type}")
    
    try:
        store = get_store()
        logger.info(f"Got store instance: {store}")
        
        result = store.ingest(tenant_id, connector_id, data_type, sample_data, metadata)
        
        logger.info(f"✅ Ingestion result: {result}")
        
        # Now query the database to verify
        verify_data(tenant_id, connector_id)
        
    except Exception as e:
        logger.error(f"❌ Ingestion failed: {e}", exc_info=True)
        return False
    
    return True

def verify_data(tenant_id: str, connector_id: str):
    """Query the database to verify data was persisted"""
    from kernel_common.persistence_v2 import PostgresBackend
    
    logger.info(f"\n🔍 Verifying data in database...")
    
    backend = PostgresBackend()
    conn = backend.get_connection()
    cursor = conn.cursor()
    
    try:
        # Check compact table
        cursor.execute("""
            SELECT data_id, tenant_id, connector_id, data_type, 
                   jsonb_array_length(data) as record_count,
                   synced_at
            FROM connectors.connector_data
            WHERE tenant_id = %s AND connector_id = %s
            ORDER BY synced_at DESC
        """, (tenant_id, connector_id))
        
        rows = cursor.fetchall()
        
        if rows:
            logger.info(f"✅ Found {len(rows)} entries in connector_data:")
            for row in rows:
                logger.info(f"  - data_id={row[0]}, type={row[3]}, records={row[4]}, synced={row[5]}")
                
            # Fetch actual data
            cursor.execute("""
                SELECT data
                FROM connectors.connector_data
                WHERE tenant_id = %s AND connector_id = %s
                ORDER BY synced_at DESC
                LIMIT 1
            """, (tenant_id, connector_id))
            
            data_row = cursor.fetchone()
            if data_row:
                logger.info(f"  📦 Latest data sample: {data_row[0][:2]}")  # First 2 records
        else:
            logger.warning(f"⚠️  No data found in connector_data for tenant={tenant_id}, connector={connector_id}")
            
        # Check chunks table
        cursor.execute("""
            SELECT chunk_id, chunk_index, 
                   jsonb_array_length(data) as record_count
            FROM connectors.connector_data_chunks
            WHERE tenant_id = %s AND connector_id = %s
            ORDER BY chunk_index
        """, (tenant_id, connector_id))
        
        chunk_rows = cursor.fetchall()
        if chunk_rows:
            logger.info(f"✅ Found {len(chunk_rows)} chunks:")
            for row in chunk_rows:
                logger.info(f"  - chunk_id={row[0]}, index={row[1]}, records={row[2]}")
        else:
            logger.info(f"ℹ️  No chunks found (expected for small datasets)")
            
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    logger.info("=" * 80)
    logger.info("CSV Ingestion Direct Test")
    logger.info("=" * 80)
    
    success = test_direct_ingestion()
    
    logger.info("=" * 80)
    if success:
        logger.info("✅ Test completed - check logs above for results")
    else:
        logger.error("❌ Test failed - check errors above")
    logger.info("=" * 80)
