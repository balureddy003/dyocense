# ERPNext Connector - Quick Start

## 🚀 5-Minute Setup

### Step 1: Generate API Keys (2 minutes)

1. **Login to ERPNext**: Open your ERPNext instance
2. **Navigate to User**: Click profile → "My Settings"  
3. **Generate Keys**: Scroll to "API Access" → Click "Generate Keys"
4. **Copy Secret**: ⚠️ IMPORTANT - Copy the API Secret NOW (shown only once!)
5. **Copy Key**: Note the API Key (visible in API Access section)

### Step 2: Add Connector in Dyocense (2 minutes)

1. **Go to Connectors**: In Dyocense, navigate to "Data Connectors"
2. **Add ERPNext**: Click "Add connector" → Select "ERPNext" card
3. **Enter Details**:
   - ERPNext URL: `https://erp.yourcompany.com`
   - API Key: `[paste from Step 1]`
   - API Secret: `[paste from Step 1]`
4. **Click Connect**: System will test connection automatically

### Step 3: Verify & Sync (1 minute)

1. **Check Status**: Connector should show "Connected" status
2. **Trigger Sync**: Click "Sync now" button
3. **View Data**: Data should appear in 30-60 seconds

✅ **Done!** Your ERPNext data is now syncing with Dyocense.

---

## 📊 What Gets Synced?

| Data Type | Details | Refresh |
|-----------|---------|---------|
| 📦 **Inventory** | Items, stock levels, reorder points | Daily |
| 🛒 **Orders** | Sales orders (last 90 days) | Daily |
| 🏭 **Suppliers** | Active suppliers, payment terms | Weekly |

---

## 🔧 Common Issues & Fixes

### ❌ "Connection Failed"

**Cause**: Invalid credentials or URL

**Fix**:

```
✓ Check ERPNext URL is correct (https://erp.example.com)
✓ Verify API Key and Secret are copied correctly
✓ Ensure user has "System Manager" role
✓ Test ERPNext URL in browser (should be accessible)
```

### ❌ "No Data Synced"

**Cause**: Insufficient permissions

**Fix**:

```
✓ User needs read access to: Item, Bin, Sales Order, Supplier
✓ Check if data exists in ERPNext (e.g., active items)
✓ Review sync logs for specific errors
```

### ❌ "API Secret Lost"

**Cause**: Secret only shown once during generation

**Fix**:

```
1. Go back to ERPNext → User Settings → API Access
2. Click "Generate Keys" again (creates NEW credentials)
3. Update connector in Dyocense with new credentials
```

---

## 💡 Pro Tips

### Best Practices

1. **Dedicated API User**: Create a separate user for API access
   - Email: `api@yourcompany.com`
   - Role: System Manager (read-only)
   - Purpose: Better audit trail

2. **Secure Storage**: Store API credentials in password manager

3. **Regular Rotation**: Change API credentials every 90 days

4. **Monitor Usage**: Check ERPNext logs for API usage patterns

### Recommended Sync Schedule

| Business Size | Frequency | Reason |
|---------------|-----------|--------|
| Small (<10 orders/day) | Daily | Sufficient for most needs |
| Medium (10-50 orders/day) | Daily | Balance freshness vs load |
| Large (>50 orders/day) | Manual + Webhook | Real-time updates |

---

## 🎯 Use Cases

### Ask Your AI Coach

Once data is synced, you can ask:

**Inventory Management:**

```
"Which items need reordering?"
"What's my total inventory value?"
"Show me items with less than 10 units in stock"
```

**Sales Analysis:**

```
"What were my sales last month?"
"Which customers ordered the most?"
"Show pending orders by customer"
```

**Supplier Insights:**

```
"List my top 5 suppliers"
"Which suppliers have NET 30 terms?"
"Show suppliers by country"
```

---

## 📞 Need Help?

- 📖 **Full Guide**: See [ERPNEXT_CONNECTOR_GUIDE.md](./ERPNEXT_CONNECTOR_GUIDE.md)
- 🔧 **Technical Docs**: See [ERPNEXT_CONNECTOR_TECHNICAL.md](./ERPNEXT_CONNECTOR_TECHNICAL.md)
- 💬 **Community**: community.dyocense.com
- 📧 **Support**: <support@dyocense.com>

---

**Version**: 1.0 | **Compatible with**: ERPNext v13, v14, v15
