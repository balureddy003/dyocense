# Connector Marketplace Demo Guide

## Quick Demo of Chat-Based Connector Configuration

This guide shows how to test the new connector marketplace feature in Dyocense.

## What's New

✨ **10 UK Small Business Connectors** ready to use
💬 **Chat-Based Setup** - No technical knowledge needed  
🏢 **Tenant-Level Storage** - Configure once, use everywhere
🔌 **MCP Support** - Connect any custom API
🤖 **AI Detection** - Automatically suggests connectors based on goals

## Testing the Feature

### 1. Start the Development Server

```bash
cd apps/ui
npm run dev
```

Open http://localhost:5173 in your browser.

### 2. Test Flow 1: Browse Connector Marketplace

1. **Open Dashboard** → You'll see the AgentAssistant panel
2. **Click "Connectors (0)"** button in the header
3. **Marketplace Opens** showing:
   - Search bar at top
   - Category tabs: Popular, Finance, E-commerce, POS, CRM, Storage, Inventory
   - Grid of 10 connectors with icons and descriptions
4. **Try Search** → Type "Xero" → See Xero Accounting highlighted
5. **Try Categories** → Click "Finance & Accounting" → See Xero, Sage, QuickBooks, Stripe
6. **View Connector Details**:
   - Hover over any connector card
   - See: OAuth2 vs API Key badge
   - See: Data types it provides (invoices, expenses, etc.)
   - See: Region (UK, Global, etc.)

### 3. Test Flow 2: Connect Xero via Chat Setup

1. **Click "Connect" on Xero** → Chat setup wizard opens
2. **Step 1: Intro**
   - AI explains what Xero data will be available
   - Shows list of data types (invoices, expenses, contacts, etc.)
   - Optional: Give connection a custom name (e.g., "Main Xero Account")
   - Click "Continue"
3. **Step 2: OAuth Explanation**
   - AI explains OAuth in simple terms: "You'll log in directly on Xero's website"
   - Shows security assurance
   - Link to setup documentation
   - Click "Continue"
4. **Step 3: Field Collection**
   - Progress bar shows "Step 1 of 3"
   - AI asks: "Let's start with your **Client ID**"
   - Field appears with placeholder: "Enter your Xero Client ID"
   - Validation: Required field, pattern check
   - **For demo**: Enter any text (e.g., "test-client-123")
   - Click "Continue"
5. **Step 4: More Fields**
   - AI asks for Client Secret
   - AI asks for Organization ID
   - Progress updates for each step
6. **Step 5: Testing**
   - AI shows: "Testing connection to Xero..."
   - Loading spinner appears
   - **Simulated delay: 2 seconds**
   - Success message: "Successfully connected to Xero!"
7. **Step 6: Return to Chat**
   - Modal closes
   - Chat shows system message: "✓ Xero Accounting connected successfully! I can now access your invoices, expenses, financial data."
   - Connectors button updates: "Connectors (1)"

### 4. Test Flow 3: View Connected Data Sources

1. **Click "Connectors (1)"** button
2. **Connected Data Sources Panel** appears showing:
   - Xero Accounting card with:
     - 🟢 Green "active" badge
     - Category: accounting
     - Last synced: just now
     - 234 records (simulated)
   - "Sync All" button at top
   - "Add" button to connect more
3. **Expand Connector Details**:
   - Click "More" on Xero card
   - See: Data types (invoices, expenses, contacts, etc.)
   - See: Sample queries you can ask
   - See: Connected time, sync frequency
4. **Test Sync**:
   - Click "Sync All" button
   - Status changes to 🔵 "syncing"
   - After 1 second: Back to 🟢 "active"
   - System message: "✓ Synced 1 data source"
5. **Disconnect**:
   - Click trash icon on connector
   - Confirm dialog appears
   - Click OK → Connector removed
   - Button updates: "Connectors (0)"

### 5. Test Flow 4: Chat-Triggered Connector Suggestion

1. **Return to Chat Mode** (click anywhere outside connectors panel or press Esc)
2. **Type in chat**: "I need to analyze my invoices"
3. **AI Detects** keyword "invoices"
4. **AI Responds**: "To analyze your financial data, I recommend connecting your accounting system."
5. **Marketplace Auto-Opens** with Finance category selected
6. **Xero, Sage, QuickBooks** are highlighted as suggestions
7. **Connect one** following the flow above

### 6. Test Flow 5: Multiple Connectors

1. **Connect Xero** (financial data)
2. **Connect Shopify** (sales data)
3. **Connect Google Drive** (spreadsheets)
4. **View all 3** in Connectors panel
5. **Check chat context**:
   - AI now says: "I have access to your: invoices from Xero; orders from Shopify; spreadsheets from Google Drive"
6. **Ask goal-related question**: "Help me improve profit margins"
7. **AI references real data**: "Based on your Xero data from last 6 months..."

### 7. Test Flow 6: Custom REST API (MCP)

1. **Open Connector Marketplace**
2. **Click "Connect" on Custom REST API**
3. **Setup wizard** shows MCP-compatible fields:
   - API Base URL
   - Authentication Method (OAuth2, API Key, Basic, None)
   - Custom Headers
   - Endpoint Configuration
4. **Enter example**:
   - Base URL: `https://api.myerp.com/v1`
   - Auth Method: API Key
   - API Key: `demo-key-123`
5. **Test connection** → Success
6. **Custom connector saved** and appears in list
7. **Badge shows**: 🔌 MCP Compatible

## Expected Behavior

### Visual Indicators

- **Connector Count Badge**: Shows `(0)`, `(1)`, `(3)` etc.
- **Status Colors**:
  - 🟢 Green = Active and syncing
  - 🔵 Blue = Currently syncing
  - 🔴 Red = Error (connection failed)
  - ⚪ Gray = Inactive

### Chat Intelligence

The AI should detect these keywords and suggest connectors:

| User Says | AI Suggests |
|-----------|-------------|
| "invoice", "expense", "accounting" | Xero, Sage, QuickBooks |
| "sales", "order", "product" | Shopify, WooCommerce, Square |
| "inventory", "stock" | Square, Shopify, Custom API |
| "customer", "lead", "deal" | HubSpot CRM |
| "spreadsheet", "google drive" | Google Drive |

### Data Context

When connectors are active, the AI should:
1. ✅ Mention available data sources in responses
2. ✅ Reference specific data ("Based on your Xero data...")
3. ✅ Suggest missing data sources for better planning
4. ✅ Show data context in blue info box on Connectors page

### LocalStorage

All connector configs are stored in localStorage:
- Key: `dyocense_tenant_connectors`
- Value: JSON array of TenantConnector objects
- **To reset**: Open DevTools → Application → Local Storage → Delete `dyocense_tenant_connectors`

## Troubleshooting

### Issue: Connector doesn't appear after setup

**Solution**: Check console for errors. Ensure:
- Valid field inputs (required fields filled)
- No TypeScript compilation errors
- LocalStorage is enabled in browser

### Issue: "Connectors (0)" doesn't update after connecting

**Solution**: 
- Refresh the component state by clicking back to Chat and then back to Connectors
- Check localStorage to verify connector was saved
- Look for console errors

### Issue: Marketplace doesn't open when clicking "Connectors"

**Solution**:
- Check that `mode` state updates to "connectors"
- Verify modal z-index is high enough (should be `z-50`)
- Check for JavaScript errors in console

### Issue: Chat doesn't suggest connectors

**Solution**:
- Try exact keywords: "invoice", "sales", "inventory"
- Check `suggestConnectorFromIntent()` function is called
- Verify `profile?.tenant_id` is set (default: "demo-tenant")

## Current Limitations (Demo Mode)

⚠️ **No Real API Calls**
- Connection testing is simulated (2-second delay)
- OAuth flow is mocked (doesn't actually redirect)
- No real data fetched from Xero, Shopify, etc.

⚠️ **LocalStorage Only**
- Configs stored in browser localStorage
- Not persisted to backend
- Lost when clearing browser data

⚠️ **No Encryption**
- API keys stored in plain text (localStorage)
- Production should encrypt with tenant-specific key

⚠️ **Simulated Sync**
- "Sync All" doesn't fetch real data
- Just updates timestamps and record counts

⚠️ **No OAuth Redirect**
- OAuth2 flow is explained but not implemented
- User enters credentials directly in form

## Production Checklist

Before going live, implement:

- [ ] Backend API endpoints (POST/GET/DELETE /v1/tenants/:id/connectors)
- [ ] Real OAuth 2.0 flow with redirect
- [ ] Encrypted credential storage
- [ ] Actual data sync from connected services
- [ ] Token refresh for expired OAuth tokens
- [ ] Rate limiting per connector
- [ ] Webhook support for real-time updates
- [ ] Error handling and retry logic
- [ ] Audit log for connector changes
- [ ] User permissions (who can connect/disconnect)

## Testing Checklist

Mark ✅ when verified:

- [ ] Marketplace opens and displays 10 connectors
- [ ] Search filters connectors correctly
- [ ] Category tabs filter by category
- [ ] Click "Connect" opens chat setup wizard
- [ ] Progress bar updates during setup
- [ ] Field validation works (required, patterns)
- [ ] Connection test shows loading then success
- [ ] Connector appears in Connected Data Sources panel
- [ ] "Connectors (N)" badge updates correctly
- [ ] Sync All button triggers sync animation
- [ ] Disconnect removes connector with confirmation
- [ ] Chat detects "invoice" keyword and suggests Xero
- [ ] Multiple connectors can be active simultaneously
- [ ] Data context prompt updates with active connectors
- [ ] Custom REST API connector can be configured
- [ ] MCP badge appears on Custom REST API
- [ ] LocalStorage persists connectors across page refresh

## Next Steps

Once demo is verified working:

1. **Backend Integration**
   - Implement `/v1/tenants/:id/connectors` API
   - Set up PostgreSQL table: `tenant_connectors`
   - Encrypt sensitive fields (API keys, tokens)

2. **OAuth Implementation**
   - Set up OAuth apps for Xero, Shopify, Google, etc.
   - Implement redirect flow
   - Handle token refresh

3. **Real Data Sync**
   - Integrate Xero API client
   - Integrate Shopify API client
   - Schedule background sync jobs
   - Cache data in database

4. **Enhanced AI**
   - Use real data in AI responses
   - Generate insights from actual numbers
   - Suggest actions based on data trends

5. **Marketplace Expansion**
   - Add more UK connectors (Revolut Business, FreeAgent, etc.)
   - Enable custom connector publishing
   - Add community ratings and reviews

## Demo Script for Stakeholders

**Scenario**: UK small business owner wants to improve cash flow

1. **Show Problem**: "I want to improve my cash flow but don't know where to start"

2. **AI Suggests**: "To analyze your cash flow, I recommend connecting your accounting system"

3. **Browse Marketplace**: Show 10 UK-focused connectors, explain why Xero is #1 choice

4. **Connect Xero**: Walk through chat-based setup, explain OAuth in simple terms

5. **Show Data Context**: AI now has access to invoices, expenses, payment data

6. **Generate Goal**: AI creates SMART goal: "Reduce average payment time from 45 days to 30 days in 3 months"

7. **Action Plan**: AI suggests specific actions based on Xero data:
   - Identify top 10 slow-paying customers
   - Set up automated payment reminders
   - Offer 2% discount for early payment

8. **Track Progress**: Show version history, compare baseline vs current performance

9. **Add More Data**: Connect Shopify for sales data, Google Drive for forecasts

10. **Holistic View**: AI combines financial + sales + forecasts for complete picture

**Key Message**: "We make data-driven business planning accessible to non-technical business owners through conversation."

## Resources

- **Code**: `/Users/balu/Projects/dyocense/apps/ui/src/`
  - `lib/connectorMarketplace.ts` - Connector catalog
  - `lib/tenantConnectors.ts` - Tenant storage & AI intelligence
  - `components/ConnectorMarketplace.tsx` - Visual marketplace
  - `components/ChatConnectorSetup.tsx` - Setup wizard
  - `components/ConnectedDataSources.tsx` - Management panel
  - `components/AgentAssistant.tsx` - Main integration

- **Documentation**: `/Users/balu/Projects/dyocense/docs/components/connectors/README.md`

- **UK Market Research**:
  - Xero: 40% market share among UK SMEs
  - Sage: 30% market share (especially Sage 50)
  - Square: Leading POS for UK hospitality/retail
  - Google Workspace: 80%+ adoption in UK businesses

**Built with ❤️ for UK small businesses**
