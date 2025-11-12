# CSV Tools Fix for Agent Data Querying

## Problem

The CSV MCP tools (Query CSV, Analyze CSV, Aggregate CSV) shown in the agent UI were **not working** because:

1. **Data mismatch**: CSV data uploaded through the UI was stored in **PostgreSQL** (`connector_data` table)
2. **Tool expectation**: CSV MCP tools were designed to read CSV **files from disk** (`/data/csv` directory)
3. **Result**: When agent tried to query data, it got "CSV file not found" errors because the files didn't exist on disk

## Root Cause

```
User uploads CSV → Stored in PostgreSQL → CSV MCP tools look for files on disk → File not found ❌
```

The upload flow stored data in the database, but the query tools expected filesystem access.

## Solution

Implemented a **dual-storage approach**:

1. **Upload CSV** → Store in PostgreSQL (for health score, analytics) **AND** export to disk (for MCP tools)
2. **CSV MCP tools** → Read from tenant-specific directories on disk
3. **Tenant isolation** → Each tenant gets their own CSV directory

```
User uploads CSV 
  ↓
  ├─→ PostgreSQL (connector_data table)  ← Used by health score
  └─→ Filesystem (/data/csv/tenant_id/)  ← Used by MCP tools ✅
```

## Changes Made

### 1. Export CSV to Disk on Upload (`services/connectors/routes.py`)

```python
# After saving to PostgreSQL, export to disk for MCP tools
csv_data_dir = os.getenv("CSV_DATA_DIR", "/data/csv")
tenant_csv_dir = os.path.join(csv_data_dir, tenant_id)
os.makedirs(tenant_csv_dir, exist_ok=True)

csv_filename = f"{connector_id}_{inferred_type}.csv"
csv_filepath = os.path.join(tenant_csv_dir, csv_filename)

with open(csv_filepath, 'w', newline='', encoding='utf-8') as csvfile:
    writer = csv_module.DictWriter(csvfile, fieldnames=header)
    writer.writeheader()
    writer.writerows(rows_data)
```

**Result**: CSV data is now available both in PostgreSQL and on disk.

### 2. Tenant-Specific CSV Directories (`services/connectors/csv_mcp.py`)

```python
# Global tenant context from CLI args
TENANT_ID: Optional[str] = None
CONNECTOR_ID: Optional[str] = None

def _get_tenant_csv_dir() -> Path:
    """Get the tenant-specific CSV directory."""
    base_path = Path(CSV_DATA_DIR)
    if TENANT_ID:
        return base_path / TENANT_ID  # /data/csv/cyclonerake-97759e/
    return base_path

def _get_csv_path(filename: str) -> Path:
    """Resolve CSV file path within tenant's directory."""
    base_path = _get_tenant_csv_dir().resolve()
    file_path = (base_path / filename).resolve()
    # Security check...
    return file_path
```

**Result**: Each tenant's CSV files are isolated in their own directory.

### 3. CLI Arguments for Tenant Context (`services/connectors/csv_mcp.py`)

```python
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="CSV MCP Server for Dyocense")
    parser.add_argument("--tenant", type=str, required=True, help="Tenant ID")
    parser.add_argument("--connector", type=str, required=True, help="Connector ID")
    args = parser.parse_args()
    
    TENANT_ID = args.tenant
    CONNECTOR_ID = args.connector
    
    logger.info(f"Starting CSV MCP server for tenant={TENANT_ID}")
    logger.info(f"Available CSV files: {_get_available_files()}")
```

**Result**: MCP server knows which tenant's data to access.

### 4. Directory Creation on Startup (`services/connectors/main.py`)

```python
def _start_csv_mcp_for(tenant_id: str, connector_id: str, data_dir: str | None = None) -> None:
    # Ensure CSV data directory exists
    csv_data_dir = data_dir or CSV_DATA_DIR
    tenant_csv_dir = os.path.join(csv_data_dir, tenant_id)
    os.makedirs(tenant_csv_dir, exist_ok=True)  # Create if needed
    
    cmd = [sys.executable, str(CSV_MCP_SCRIPT), "--tenant", tenant_id, "--connector", connector_id]
    env = os.environ.copy()
    env["CSV_DATA_DIR"] = csv_data_dir
```

**Result**: Directories are automatically created when needed.

## File Structure

```
/data/csv/
  ├── cyclonerake-97759e/          ← Tenant ID
  │   ├── conn-123_products.csv     ← Connector ID + Data Type
  │   ├── conn-123_orders.csv
  │   └── conn-456_inventory.csv
  ├── another-tenant-id/
  │   └── conn-789_products.csv
  └── ...
```

## How It Works Now

### Upload Flow

```
1. User uploads products.csv via UI
2. Frontend → POST /api/connectors/upload_csv
3. Backend:
   a. Parse CSV data
   b. Store in PostgreSQL (connector_data table)
   c. Export to /data/csv/cyclonerake-97759e/conn-123_products.csv
4. Return success to UI
```

### Query Flow (Agent)

```
1. Agent asks "What products do I have?"
2. Agent uses "Query CSV" tool with filename="conn-123_products.csv"
3. CSV MCP server:
   a. Reads from /data/csv/cyclonerake-97759e/conn-123_products.csv
   b. Returns product data
4. Agent responds with product information
```

## Testing

### 1. Verify CSV Export

```bash
# After uploading CSV through UI, check if file exists
ls -la /data/csv/cyclonerake-97759e/

# Should see files like:
# conn-abc123_products.csv
# conn-abc123_orders.csv
```

### 2. Test CSV Tools in Agent

1. Upload a CSV file via Connectors page
2. Open Chat/Agent interface
3. Click Tools dropdown → should see "Query CSV", "Analyze CSV", etc.
4. Ask agent: "What data do I have?"
5. Agent should list available CSV files
6. Ask: "Show me the first 5 rows of products"
7. Agent should successfully query and display data

### 3. Check MCP Server Logs

```bash
# Look for CSV MCP server startup
# Should see:
# "Starting CSV MCP server for tenant=cyclonerake-97759e"
# "Available CSV files: ['conn-123_products.csv']"
```

## Benefits

✅ **No Breaking Changes**: PostgreSQL storage still works for health scores  
✅ **Tenant Isolation**: Each tenant's CSV files are separate  
✅ **Security**: Path validation prevents directory traversal  
✅ **Agent Tools Work**: CSV tools can now query uploaded data  
✅ **Automatic**: Export happens automatically on upload  

## Environment Variables

- `CSV_DATA_DIR`: Base directory for CSV files (default: `/data/csv`)
- Can be customized per deployment

## Future Improvements

1. **Cleanup**: Add cron job to delete old CSV files
2. **Size Limits**: Add file size validation to prevent disk issues
3. **Direct PostgreSQL Access**: Create tools that query PostgreSQL directly (alternative approach)
4. **File Sync**: Option to sync from PostgreSQL to disk on service startup
