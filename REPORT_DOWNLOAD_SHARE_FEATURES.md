# Report Download & Agent Thinking Features

## Overview

Added comprehensive report generation capabilities with agent reasoning transparency and multiple download/share options.

## Features Implemented

### 1. **Agent Thinking Display** 🤖

Shows detailed step-by-step reasoning process for each analysis:

- **Thought**: What the agent is thinking ("I need to calculate total inventory value")
- **Action**: What action it takes ("Multiplying Quantity by UnitPrice for each product")
- **Observation**: What it discovers ("Total inventory worth $1,200,000")
- **Data Source**: Which data it used ("inventory" table)

**Example**:

```
Agent: Volume Analysis Agent
💭 Thought: I need to calculate the total inventory volume
⚡ Action: Summed all Quantity values from 4,338 products
👁️ Observation: Total volume is 541,909 units with average of 125.0 per product
📊 Data Source: inventory
```

### 2. **Evidence & Calculations** 📊

Every claim in the report is backed by evidence:

- **Claim**: "Total unique products: 4,338"
- **Calculation**: `COUNT(DISTINCT StockCode)`
- **Value**: 4,338
- **Confidence**: 100%
- **Data Source**: inventory

This makes reports trustworthy and auditable.

### 3. **Download Report** 📥

Download analysis reports in multiple formats:

#### **HTML Format** (Recommended)

- Rich, styled report with colors and formatting
- Includes agent thinking and evidence sections
- Print-ready
- Example filename: `Business_Analysis_Report_RPT-20241115-143052.html`

#### **Markdown Format**

- Plain text with markdown formatting
- Easy to edit in any text editor
- Git-friendly
- Great for documentation

#### **JSON Format**

- Structured data format
- Can be processed programmatically
- Includes all metadata
- Perfect for integrations

### 4. **Share Report** 🔗

Generate shareable links for reports:

- **Expiry**: Links expire after 7 days (configurable)
- **Public access**: No authentication required
- **View tracking**: Tracks how many times link was accessed
- **Secure**: Each share has unique token

**Example share URL**:

```
https://yourapp.com/api/v1/public/reports/share-a1b2c3d4e5f6g7h8
```

### 5. **Report Metadata** 📋

Each report includes:

- Report ID (e.g., `RPT-20241115-143052-a3f9e2`)
- Generation timestamp
- Original query
- Business name
- Report type
- Number of sections
- Total evidence count
- Total agent thoughts count

## API Endpoints

### Download Report

```http
POST /v1/tenants/{tenant_id}/reports/download
Content-Type: application/json

{
  "report_id": "RPT-20241115-143052-a3f9e2",
  "format": "html",
  "include_thinking": true,
  "include_evidence": true
}
```

**Response**: File download (HTML/JSON/Markdown)

### Share Report

```http
POST /v1/tenants/{tenant_id}/reports/share
Content-Type: application/json

{
  "report_id": "RPT-20241115-143052-a3f9e2",
  "expiry_days": 7
}
```

**Response**:

```json
{
  "share_url": "/v1/public/reports/share-abc123",
  "share_token": "share-abc123",
  "expires_at": "2024-11-22T14:30:52Z",
  "report_id": "RPT-20241115-143052-a3f9e2"
}
```

### Access Shared Report

```http
GET /v1/public/reports/{share_token}?format=html
```

No authentication required. Returns report if link is valid and not expired.

### List Reports

```http
GET /v1/tenants/{tenant_id}/reports?limit=10
```

**Response**:

```json
{
  "reports": [
    {
      "report_id": "RPT-20241115-143052-a3f9e2",
      "title": "Business Analysis Report",
      "report_type": "comprehensive_analysis",
      "generated_at": "2024-11-15T14:30:52Z",
      "query": "please do detailed product stock analysis",
      "sections_count": 5,
      "has_shares": true
    }
  ]
}
```

## Frontend Components

### ReportDownloadButtons Component

```tsx
<ReportDownloadButtons
  reportId="RPT-20241115-143052-a3f9e2"
  tenantId="tenant_123"
  reportTitle="Business Analysis Report"
/>
```

Features:

- **Download menu** with format options (HTML/Markdown/JSON)
- **Share button** generates shareable link
- **Copy link** button with confirmation
- **Expiry notice** shows when link expires

## Report Structure

### HTML Report Sections

1. **Header**
   - Report title with emoji
   - Business name
   - Generation date
   - Report ID

2. **Executive Summary**
   - High-level overview
   - Key findings
   - Overall status

3. **Analysis Sections** (for each task executed):
   - Section title (e.g., "📊 Data Discovery")
   - Content/findings
   - **Agent Thoughts** (if enabled):
     - Agent name
     - Thought → Action → Observation flow
     - Data source used
   - **Evidence & Calculations** (if enabled):
     - Claims with supporting data
     - Calculation formulas
     - Confidence levels
   - **Key Insights** (bullet points)
   - **Recommended Actions** (numbered list)

4. **Footer**
   - Report metadata
   - Generation info
   - Branding

### Styling

- **Gradient headers**: Purple to violet gradient
- **Color-coded sections**:
  - Agent thoughts: Warm yellow background
  - Evidence: Cool green background
  - Insights: Light gray background
  - Recommendations: Light blue background
- **Responsive design**: Works on mobile and desktop
- **Print-ready**: Hides download buttons when printing

## How It Works

### Step-by-Step Flow

1. **User asks question**: "please do detailed product stock analysis"

2. **Task execution** (Phase 1):

   ```
   🔍 Discovering data structure ✓
   📦 Analyzing inventory volume ✓
   💰 Calculating inventory value ✓
   ⭐ Identifying top products ✓
   ⚠️ Detecting stock issues ✓
   ```

3. **Report generation** (Phase 1.5):
   - System creates `BusinessReport` object
   - Adds sections from each completed task
   - Extracts agent thoughts and evidence from task results
   - Generates unique report ID
   - Stores report in `TENANT_REPORTS` dictionary

4. **Progress message**:

   ```
   📊 Report Generated: [Download Report] | Report ID: RPT-...
   ```

5. **Coach analysis** (Phase 2):
   - Coach interprets results
   - Generates natural language summary
   - Provides recommendations

6. **Frontend display**:
   - Shows coach response
   - Displays download/share buttons
   - User can download in any format
   - User can generate shareable link

## Code Changes

### Backend Files

1. **`services/smb_gateway/report_generator.py`**
   - Added `AgentThought` class
   - Added `Evidence` class
   - Enhanced `ReportSection` with agent_thoughts and evidence
   - Added `to_html()` method with styling
   - Enhanced `to_markdown()` with thinking and evidence sections

2. **`services/smb_gateway/main.py`**
   - Added report download endpoint
   - Added share report endpoint
   - Added access shared report endpoint
   - Added list reports endpoint
   - Integrated report generation into streaming chat
   - Stores reports in `TENANT_REPORTS` dictionary

3. **`services/smb_gateway/task_planner.py`**
   - Methods return agent_thoughts and evidence in results
   - (Future enhancement - currently need to add this)

### Frontend Files

1. **`apps/smb/src/components/ReportDownloadButtons.tsx`** (NEW)
   - Download menu with format selection
   - Share button with link generation
   - Copy button with confirmation
   - Expiry notice

2. **`apps/smb/src/pages/CoachV4.tsx`**
   - Added `reportId` field to Message interface
   - Captures report_id from streaming metadata
   - Displays `ReportDownloadButtons` when report generated
   - Shows download buttons below assistant messages

## Future Enhancements

### Phase 2 (Recommended)

1. **PDF Generation**
   - Add weasyprint library
   - Convert HTML to PDF server-side
   - Better formatting for print

2. **Database Storage**
   - Move from in-memory to PostgreSQL
   - Persist reports across restarts
   - Add cleanup for expired shares

3. **Enhanced Evidence**
   - Add data samples to evidence
   - Show before/after comparisons
   - Include chart images in reports

4. **Report Templates**
   - Custom report styles
   - Business-specific branding
   - Configurable sections

5. **Email Reports**
   - Send reports via email
   - Schedule recurring reports
   - Email share links

6. **Report History**
   - Compare reports over time
   - Track metric changes
   - Historical analysis

## Testing

### Test Report Generation

```bash
curl -X POST http://localhost:8000/v1/tenants/test_tenant/coach/chat/stream \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer test_token" \
  -d '{
    "message": "please do detailed product stock analysis",
    "conversation_history": []
  }'
```

Look for:

- Progress markers: `✓`
- Report generated message: `📊 Report Generated`
- Report ID in response

### Test Download

```bash
curl -X POST http://localhost:8000/v1/tenants/test_tenant/reports/download \
  -H "Content-Type: application/json" \
  -d '{
    "report_id": "RPT-20241115-143052-a3f9e2",
    "format": "html",
    "include_thinking": true,
    "include_evidence": true
  }' \
  -o report.html
```

### Test Share

```bash
curl -X POST http://localhost:8000/v1/tenants/test_tenant/reports/share \
  -H "Content-Type: application/json" \
  -d '{
    "report_id": "RPT-20241115-143052-a3f9e2",
    "expiry_days": 7
  }'
```

## Benefits

1. **Transparency**: Users see exactly how agents analyzed their data
2. **Trust**: Every claim backed by evidence and calculations
3. **Auditability**: Full trail of reasoning and data sources
4. **Shareability**: Easy to share insights with stakeholders
5. **Flexibility**: Multiple formats for different use cases
6. **Professionalism**: Beautiful, styled reports ready for presentation

## Example Output

### Agent Thinking Section

```
🤖 How Our Agents Analyzed This

Agent: Schema Discovery Agent
💭 Thought: I need to understand the structure of inventory data to perform accurate analysis
⚡ Action: Analyzing 541,909 records to identify fields and data types
👁️ Observation: Found 541,909 records in inventory
📊 Data Source: inventory

Agent: Schema Discovery Agent
💭 Thought: I need to identify key fields for analysis
⚡ Action: Inspected field types: InvoiceNo, StockCode, Description, Quantity, UnitPrice
👁️ Observation: Discovered 8 fields with various data types
📊 Data Source: inventory
```

### Evidence Section

```
📊 Evidence & Calculations

Analyzed 541,909 inventory records
Source: inventory | Calculation: COUNT(records) | Confidence: 100%

Total unique products: 4,338
Source: inventory | Calculation: COUNT(DISTINCT StockCode) | Confidence: 100%

Total quantity across all products: 541,909
Source: inventory | Calculation: SUM(Quantity) | Confidence: 100%
```

This creates a GitHub Copilot-like experience where users understand not just WHAT the system found, but HOW and WHY it reached those conclusions.
