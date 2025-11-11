# ERPNext Connector - Technical Implementation

## Overview

The ERPNext connector provides seamless integration between Dyocense and ERPNext ERP systems using the official Frappe REST API.

## Architecture

```
┌─────────────────┐
│   Dyocense UI   │
│  (React/Mantine)│
└────────┬────────┘
         │ HTTPS
         ▼
┌─────────────────┐
│ Connector API   │
│   (FastAPI)     │
└────────┬────────┘
         │ Token Auth
         ▼
┌─────────────────┐
│   ERPNext API   │
│ (Frappe v14+)   │
└─────────────────┘
```

## Files Structure

```
dyocense/
├── services/connectors/
│   ├── erpnext.py              # Core connector implementation
│   ├── routes.py                # API endpoints
│   └── main.py                  # Service entry point
├── apps/smb/src/pages/
│   └── Connectors.tsx           # Frontend UI
├── docs/
│   └── ERPNEXT_CONNECTOR_GUIDE.md  # User documentation
└── tests/
    └── test_erpnext_connector.py   # Test suite
```

## Backend Implementation

### Core Connector (`services/connectors/erpnext.py`)

**Key Components:**

1. **ERPNextConfig** - Pydantic model for configuration

   ```python
   class ERPNextConfig(BaseModel):
       api_url: str                 # ERPNext instance URL
       api_key: str                 # API Key
       api_secret: str              # API Secret
       sync_inventory: bool = True
       sync_orders: bool = True
       sync_suppliers: bool = True
       lookback_days: int = 90      # For orders
   ```

2. **ERPNextConnector** - Main connector class
   - Async context manager for connection lifecycle
   - Token-based authentication (api_key:api_secret)
   - Automatic session management

3. **Data Fetching Methods:**
   - `fetch_inventory()` - Items + Bin (stock) data
   - `fetch_orders()` - Sales Orders
   - `fetch_suppliers()` - Supplier master data
   - `test_connection()` - Authentication verification

### API Endpoints (`services/connectors/routes.py`)

**POST /api/connectors/erpnext/setup**

- Setup new ERPNext connector
- Validates credentials (optional - can be disabled)
- Stores encrypted configuration

**POST /api/connectors/sync**

- Triggers sync for any connector type
- Handles ERPNext-specific sync logic
- Saves data to PostgreSQL

**GET /api/connectors/status**

- Returns connector status, last sync time, record counts

### Authentication

Uses Frappe's token-based authentication:

```python
headers = {
    'Authorization': f'token {api_key}:{api_secret}',
    'Content-Type': 'application/json'
}
```

This is passed with every API request to ERPNext.

## Frontend Implementation

### Connector Configuration UI (`apps/smb/src/pages/Connectors.tsx`)

**ERPNext Preset:**

```typescript
{
    id: 'erpnext',
    label: 'ERPNext',
    description: 'Connect your ERPNext ERP system...',
    icon: '⚙️',
    category: 'erp',
    fields: [
        { name: 'api_url', label: 'ERPNext URL', ... },
        { name: 'api_key', label: 'API Key', ... },
        { name: 'api_secret', label: 'API Secret', type: 'textarea', ... }
    ]
}
```

**Modal Features:**

- Grid-based connector selection (scalable for 50+ connectors)
- Dynamic form fields based on connector type
- Helper text with setup instructions
- Sync frequency selection (Manual, Daily, Weekly)

## Data Models

### Inventory Item

```typescript
{
    item_code: string
    item_name: string
    item_group: string
    stock_qty: number
    available_qty: number
    reorder_level: number
    reorder_qty: number
    unit_price: number
    last_purchase_rate: number
    uom: string
    needs_reorder: boolean
}
```

### Sales Order

```typescript
{
    order_id: string
    customer_name: string
    customer_id: string
    order_date: string
    delivery_date: string
    total_amount: number
    net_amount: number
    advance_paid: number
    quantity: number
    status: string
    currency: string
    is_delivered: boolean
    is_pending: boolean
}
```

### Supplier

```typescript
{
    supplier_id: string
    supplier_name: string
    supplier_group: string
    supplier_type: string
    country: string
    tax_id: string
    payment_terms: string
    currency: string
    on_hold: boolean
    is_active: boolean
}
```

## ERPNext API Reference

### Base URL

```
{api_url}/api
```

### Authentication Endpoint

```
GET /api/method/frappe.auth.get_logged_user
```

Returns logged-in user email if authentication is successful.

### Resource Endpoints

**Items:**

```
GET /api/resource/Item?fields=["name","item_code","item_name",...]
```

**Stock (Bins):**

```
GET /api/resource/Bin?filters=[["item_code","=","ITEM001"]]
```

**Sales Orders:**

```
GET /api/resource/Sales Order?filters=[["transaction_date",">=","2024-01-01"]]
```

**Suppliers:**

```
GET /api/resource/Supplier?filters=[["disabled","=",0]]
```

### Query Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `fields` | JSON Array | Fields to fetch |
| `filters` | JSON Array | Filter conditions `[field, operator, value]` |
| `or_filters` | JSON Array | OR filter conditions |
| `order_by` | String | Sort order `field asc/desc` |
| `limit_page_length` | Integer | Records per page (max 1000) |
| `limit_start` | Integer | Pagination offset |

## Error Handling

### Connection Errors

```python
try:
    async with ERPNextConnector(config) as connector:
        await connector.test_connection()
except Exception as e:
    # Handle: Invalid credentials, network errors, etc.
    logger.error(f"Connection failed: {e}")
```

### API Errors

- 401 Unauthorized: Invalid API key/secret
- 403 Forbidden: Insufficient permissions
- 404 Not Found: Invalid endpoint or DocType
- 500 Server Error: ERPNext internal error

## Testing

### Run Test Suite

```bash
# Test with real ERPNext instance
python tests/test_erpnext_connector.py \
    --url https://erp.yourcompany.com \
    --key YOUR_API_KEY \
    --secret YOUR_API_SECRET

# Test specific component
python tests/test_erpnext_connector.py \
    --url https://erp.yourcompany.com \
    --key YOUR_API_KEY \
    --secret YOUR_API_SECRET \
    --test inventory

# Use mock/demo instance
python tests/test_erpnext_connector.py --mock
```

### Test Coverage

- ✅ Connection authentication
- ✅ Inventory data fetch
- ✅ Sales orders fetch
- ✅ Suppliers fetch
- ✅ Full sync workflow
- ✅ Error handling
- ✅ Data transformation

## Performance Considerations

### Batch Size

- Default: 1000 records per request
- Adjustable via `limit_page_length` parameter
- Consider ERPNext server capacity

### Rate Limiting

- Frappe doesn't enforce strict rate limits by default
- Respect server resources (don't hammer the API)
- Use pagination for large datasets

### Caching

- Connector data cached in PostgreSQL
- Reduces API calls to ERPNext
- Configurable sync frequency

### Optimization Tips

1. **Selective Fields**: Only fetch fields you need
2. **Filters**: Apply filters at API level, not in memory
3. **Pagination**: Use for large datasets (>1000 records)
4. **Async Operations**: All API calls are async (non-blocking)

## Security

### Credential Storage

- API keys/secrets encrypted at rest
- Never logged or exposed in responses
- Stored in PostgreSQL with encryption

### API Communication

- All requests use HTTPS
- Token-based authentication (no password)
- Credentials never sent in URL params

### Permissions

- Requires read-only access to DocTypes
- No write/delete permissions needed
- Can use dedicated API user with limited roles

## Deployment

### Environment Variables

```bash
# PostgreSQL for connector data storage
POSTGRES_URL=postgresql://user:pass@localhost:5432/dyocense

# Optional: Enable MongoDB instead
USE_MONGODB=false
MONGO_URI=mongodb://localhost:27017

# API service config
CONNECTORS_SERVICE_PORT=8003
```

### Docker Setup

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY services/connectors/ ./services/connectors/
COPY packages/ ./packages/

CMD ["uvicorn", "services.connectors.main:app", "--host", "0.0.0.0", "--port", "8003"]
```

### Health Check

```bash
curl http://localhost:8003/health
```

## Troubleshooting

### Common Issues

**Issue**: "Connection failed - check credentials"

```python
# Verify API credentials are correct
# Check ERPNext URL is accessible
# Ensure HTTPS is used
```

**Issue**: "No data returned"

```python
# Check user permissions on DocTypes
# Verify data exists in ERPNext (e.g., active items)
# Review filters (disabled items excluded by default)
```

**Issue**: "SSL Certificate Error"

```python
# Ensure ERPNext has valid SSL certificate
# For self-hosted, verify cert is properly configured
```

### Debug Mode

Enable debug logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

View executed queries:

```
GET /api/resource/Item?debug=True
```

Response includes executed SQL and timing.

## Future Enhancements

### Planned Features

- [ ] Purchase Orders sync
- [ ] Customer master data
- [ ] Stock Entry transactions
- [ ] Real-time webhooks (instead of polling)
- [ ] Custom field mapping
- [ ] Multi-warehouse filtering
- [ ] Incremental sync (delta only)

### API Improvements

- [ ] GraphQL support (if Frappe adds it)
- [ ] Bulk operations API
- [ ] Streaming responses for large datasets

## Resources

### Documentation

- [Frappe REST API Docs](https://docs.frappe.io/framework/v14/user/en/api/rest)
- [ERPNext Documentation](https://docs.erpnext.com)
- [User Guide](./ERPNEXT_CONNECTOR_GUIDE.md)

### Support

- GitHub Issues: [dyocense/issues](https://github.com/dyocense/dyocense/issues)
- Community Forum: community.dyocense.com
- Email: <support@dyocense.com>

---

**Last Updated**: November 2025  
**Version**: 1.0  
**Maintainers**: Dyocense Platform Team
