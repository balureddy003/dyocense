# ERPNext Connector Guide

## Overview

The ERPNext connector integrates your ERPNext ERP system with Dyocense to automatically sync:

- **Inventory**: Stock levels, reorder points, item details
- **Sales Orders**: Customer orders, revenue, delivery tracking
- **Suppliers**: Vendor information, payment terms

This connector uses the official [Frappe REST API](https://docs.frappe.io/framework/v14/user/en/api/rest) for secure, reliable data synchronization.

---

## Prerequisites

1. **ERPNext Instance**: You need a running ERPNext instance (cloud or self-hosted)
2. **User Account**: Admin or user with appropriate permissions
3. **API Access**: Ability to generate API keys (requires "System Manager" role)

---

## Setup Instructions

### Step 1: Generate API Keys in ERPNext

1. **Log in to ERPNext** as a user with System Manager role
2. **Navigate to User Settings**:
   - Click your profile picture (top right)
   - Select "My Settings" or go to User list
   - Open your user record
3. **Generate API Keys**:
   - Scroll to "API Access" section
   - Click "Generate Keys" button
   - **IMPORTANT**: Copy the API Secret immediately - it's only shown once!
4. **Save the credentials**:
   - API Key: Visible in the API Access section (stays visible)
   - API Secret: Only shown once in popup (save to password manager)

### Step 2: Configure Connector in Dyocense

1. Go to **Data Connectors** page in Dyocense
2. Click **"Add connector"**
3. Select **ERPNext** from the connector types
4. Fill in the configuration:

   ```
   ERPNext URL: https://erp.yourcompany.com
   API Key: [your-api-key]
   API Secret: [your-api-secret]
   ```

5. Click **"Connect"**

### Step 3: Verify Connection

The connector will:

1. Test authentication using `/api/method/frappe.auth.get_logged_user`
2. Verify you have access to the ERPNext instance
3. Show connection status

---

## What Data Gets Synced?

### 📦 Inventory (Items)

**Source DocType**: `Item` + `Bin`

**Fields Synced**:

- Item Code, Name, Group
- Stock Quantity (actual, available, reserved)
- Reorder Level & Quantity
- Unit Price, Last Purchase Rate
- Unit of Measurement (UOM)
- Reorder flag (automatic calculation)

**Use Case**:

- Track which products need reordering
- Monitor stock levels across warehouses
- Analyze inventory value

### 🛒 Sales Orders

**Source DocType**: `Sales Order`

**Fields Synced**:

- Order ID, Customer Name
- Order & Delivery Dates
- Total Amount, Net Amount
- Advance Paid, Status
- Quantity, Currency

**Filters**: Last 90 days by default (configurable)

**Use Case**:

- Revenue tracking
- Delivery performance
- Customer order patterns

### 🏭 Suppliers

**Source DocType**: `Supplier`

**Fields Synced**:

- Supplier Name, ID, Group
- Country, Tax ID
- Payment Terms, Currency
- On-Hold status, Active status

**Filters**: Only active (not disabled) suppliers

**Use Case**:

- Vendor management
- Payment term analysis
- Supplier performance tracking

---

## API Details

### Authentication

The connector uses **Token-based authentication**:

```
Authorization: token api_key:api_secret
```

This is the recommended method for server-to-server integrations.

### API Endpoints Used

| Purpose | Endpoint | Method |
|---------|----------|--------|
| Test Connection | `/api/method/frappe.auth.get_logged_user` | GET |
| Fetch Items | `/api/resource/Item` | GET |
| Fetch Stock | `/api/resource/Bin` | GET |
| Fetch Orders | `/api/resource/Sales Order` | GET |
| Fetch Suppliers | `/api/resource/Supplier` | GET |

### Query Parameters

The connector uses these parameters for efficient data retrieval:

```javascript
{
  fields: ["field1", "field2", ...],     // Specify which fields to fetch
  filters: [["field", "=", "value"]],   // Filter records
  limit_page_length: 1000,              // Pagination
  order_by: "field desc"                // Sorting
}
```

### Rate Limits

Frappe/ERPNext doesn't have strict rate limits by default, but:

- Be respectful of your server resources
- Dyocense syncs in batches to avoid overload
- Default sync frequency: Daily (configurable to Manual or Weekly)

---

## Permissions Required

The API user needs these permissions in ERPNext:

| DocType | Read | Write |
|---------|------|-------|
| Item | ✅ | ❌ |
| Bin | ✅ | ❌ |
| Sales Order | ✅ | ❌ |
| Supplier | ✅ | ❌ |

**Note**: Read-only access is sufficient. Dyocense does NOT write back to ERPNext.

---

## Troubleshooting

### Connection Failed

**Problem**: "Failed to connect to ERPNext API"

**Solutions**:

1. Verify ERPNext URL is correct and accessible
2. Check API Key and Secret are copied correctly
3. Ensure the user has System Manager role
4. Check firewall/network allows outbound connections
5. Verify ERPNext instance is running

### No Data Synced

**Problem**: Connection successful but no data appears

**Solutions**:

1. Check user permissions for DocTypes (Item, Sales Order, Supplier)
2. Verify data exists in ERPNext (e.g., active items, recent orders)
3. Check filters (e.g., disabled items are excluded)
4. Review sync logs for errors

### API Secret Lost

**Problem**: "I lost my API Secret"

**Solution**:

1. Go back to User Settings → API Access
2. Click "Generate Keys" again
3. This will create NEW credentials (old ones are invalidated)
4. Update the connector configuration with new credentials

### SSL/Certificate Errors

**Problem**: SSL certificate verification failed

**Solutions**:

1. Ensure ERPNext has valid SSL certificate
2. If self-hosted, ensure certificate is properly configured
3. For development: Check if ERPNext is accessible via HTTPS

---

## Data Sync Schedule

### Sync Frequency Options

- **Manual**: Sync only when you trigger it manually
- **Daily**: Automatic sync once per day (2 AM UTC)
- **Weekly**: Automatic sync once per week (Sunday 2 AM UTC)

### Manual Sync

To trigger a manual sync:

1. Go to Data Connectors page
2. Find your ERPNext connector
3. Click "Sync now" button

### What Happens During Sync?

1. **Authentication**: Verify API credentials
2. **Fetch Inventory**: Get all active items + stock levels
3. **Fetch Orders**: Get sales orders from last 90 days
4. **Fetch Suppliers**: Get all active suppliers
5. **Store Data**: Save to Dyocense database
6. **Update Timestamp**: Record last sync time

Average sync time: 30-60 seconds (depends on data volume)

---

## Security Best Practices

1. **Never share API credentials** in plain text (email, Slack, etc.)
2. **Use a dedicated API user** instead of your personal account
3. **Limit permissions** to only what's needed (read-only)
4. **Rotate credentials** periodically (every 90 days)
5. **Monitor API usage** in ERPNext logs
6. **Use HTTPS** for all API communications

---

## Advanced Configuration

### Custom Lookback Period

Default: Last 90 days of sales orders

To change this, contact support or modify connector settings:

```json
{
  "lookback_days": 180  // Last 6 months
}
```

### Selective Sync

You can enable/disable specific data types:

```json
{
  "sync_inventory": true,
  "sync_orders": true,
  "sync_suppliers": false  // Skip suppliers
}
```

### Warehouse Filtering

To sync only specific warehouses, add filter:

```json
{
  "warehouse_filter": ["Main Store", "Warehouse 1"]
}
```

---

## Integration with Dyocense AI Coach

Once ERPNext data is synced, your AI Coach can:

1. **Inventory Insights**:
   - "Which items need reordering?"
   - "What's my total inventory value?"
   - "Show me slow-moving items"

2. **Sales Analysis**:
   - "What were my sales last month?"
   - "Which customers ordered the most?"
   - "Show pending orders"

3. **Supplier Management**:
   - "List my top suppliers"
   - "Which suppliers have payment issues?"
   - "Show suppliers by region"

---

## Support & Resources

### Official Documentation

- [Frappe REST API](https://docs.frappe.io/framework/v14/user/en/api/rest)
- [ERPNext Documentation](https://docs.erpnext.com)
- [Frappe Framework](https://frappeframework.com)

### Dyocense Resources

- Community Forum: [community.dyocense.com]
- Support Email: <support@dyocense.com>
- API Status: status.dyocense.com

### Common Links

- [How to Generate API Keys](https://docs.erpnext.com/docs/v14/user/manual/en/api)
- [ERPNext User Permissions](https://docs.erpnext.com/docs/v14/user/manual/en/setting-up/users-and-permissions)

---

## Changelog

### Version 1.0 (Current)

- Initial ERPNext connector release
- Support for Inventory, Sales Orders, Suppliers
- Token-based authentication
- Daily/Weekly/Manual sync options
- Read-only access (no write-back)

### Roadmap

- [ ] Purchase Orders sync
- [ ] Customer master data sync
- [ ] Stock movements/transactions
- [ ] Real-time webhooks (instead of polling)
- [ ] Custom field mapping
- [ ] Multi-warehouse advanced filtering

---

## Example Use Cases

### Scenario 1: Inventory Reorder Alerts

**Setup**:

1. Connect ERPNext with inventory sync enabled
2. Sync runs daily at 2 AM
3. Ask Coach: "What items are below reorder level?"

**Result**: Coach analyzes inventory data and provides list of items needing reorder with suggested quantities.

### Scenario 2: Monthly Sales Review

**Setup**:

1. Connect ERPNext with sales orders sync
2. Sync runs weekly
3. Ask Coach: "Summarize my sales performance this month"

**Result**: Coach aggregates order data, calculates totals, identifies trends, and provides insights.

### Scenario 3: Supplier Payment Analysis

**Setup**:

1. Connect ERPNext with supplier sync
2. Sync runs monthly
3. Ask Coach: "Which suppliers have NET 30 payment terms?"

**Result**: Coach filters suppliers by payment terms and provides actionable list.

---

## FAQ

**Q: Does Dyocense modify my ERPNext data?**  
A: No. The connector is read-only. It never writes, updates, or deletes data in ERPNext.

**Q: How often should I sync?**  
A: For most businesses, daily sync is sufficient. Use manual sync for testing or hourly needs.

**Q: Can I sync multiple ERPNext instances?**  
A: Yes! Add multiple connectors with different credentials for each instance.

**Q: What if my ERPNext is on a private network?**  
A: You'll need to expose the API endpoint or use a VPN/tunnel solution.

**Q: Is my data encrypted?**  
A: Yes. API credentials are encrypted at rest, and all API calls use HTTPS.

**Q: Can I see sync logs?**  
A: Yes. Check the connector details page for sync history and error logs.

---

**Last Updated**: November 2025  
**Connector Version**: 1.0  
**Compatible with**: ERPNext v13, v14, v15
