# Testing the Enhanced Business Coach

## 🚀 Quick Start

### 1. Start the Services

**Terminal 1 - Backend (SMB Gateway):**

```bash
cd /Users/balu/Projects/dyocense
source .venv/bin/activate
python -m uvicorn services.smb_gateway.main:app --reload --host 127.0.0.1 --port 8000
```

**Terminal 2 - Frontend:**

```bash
cd /Users/balu/Projects/dyocense/apps/smb
npm run dev
```

### 2. Open the Coach

Navigate to: <http://localhost:5173/coach>

---

## 🎯 Features to Test

### ⚙️ Open Settings Panel

1. Look for the **⚙️ gear icon** in the top-right of the header
2. Click it to open the settings modal
3. You should see 5 sections:
   - **Select Your Coach** (5 persona cards)
   - **Data Sources** (checkboxes)
   - **Knowledge Files** (upload button)
   - **Advanced Options** (toggles)
   - **Current Configuration** (summary)

### 👤 Test Persona Selection

1. Open settings
2. Click on different persona cards:
   - **📊 Business Analyst** (analytical, data-focused)
   - **🔬 Data Scientist** (predictive, statistical)
   - **💼 Consultant** (strategic, frameworks)
   - **⚙️ Operations Manager** (efficiency, processes)
   - **🚀 Growth Strategist** (revenue, scaling)
3. Notice the blue border on selected persona
4. Close modal
5. Check header - should show active persona badge
6. Ask a question - response should match persona style

### 🎛️ Test Data Source Filtering

1. Open settings
2. Scroll to "Data Sources" section
3. Check/uncheck different sources:
   - Orders & Revenue
   - Inventory Management
   - Customer Data
4. Notice record counts for each source
5. Close modal
6. Check header - badge shows selected source count
7. Ask a question - should only use selected data

### 📄 Test File Upload

1. Open settings
2. Scroll to "Knowledge Files" section
3. Click "Upload Document" button
4. Select a PDF/TXT file
5. File should appear in uploaded list with:
   - File name
   - Size in KB
   - Upload date
6. ✕ button to remove file

### 🔬 Test Advanced Options

1. Open settings
2. Scroll to "Advanced Options"
3. Toggle **Include Evidence Citations**:
   - ON: Responses include data sources
   - OFF: Plain responses without citations
4. Toggle **Include Forecasting**:
   - ON: Adds predictive analytics
   - OFF: Historical data only

---

## 💬 Example Questions by Persona

### 📊 Business Analyst

```
"What are my top 3 KPIs?"
"How does this month compare to last month?"
"Which metrics need attention?"
```

### 🔬 Data Scientist

```
"What will my revenue be next month?"
"What's the confidence interval for my forecast?"
"Which products will have highest demand?"
```

### 💼 Consultant

```
"What's my growth strategy?"
"How should I prioritize my initiatives?"
"What are industry best practices?"
```

### ⚙️ Operations Manager

```
"How can I optimize my inventory?"
"What's causing my stockouts?"
"How do I reduce operational costs?"
```

### 🚀 Growth Strategist

```
"How can I 10x my revenue?"
"What growth levers should I pull?"
"How do I scale my business?"
```

---

## 🔍 What to Look For

### Visual Changes

**Header:**

```
Before: ✨ AI ASSISTANT
        Business Coach

After:  ✨ AI ASSISTANT                    [2 sources] ⚙️
        Business Coach [📊 Business Analyst]
```

**Settings Modal:**

- Clean, organized layout
- Visual persona cards with emojis
- Checkboxes for data sources
- File upload interface
- Current config summary at bottom

**Response Quality:**

- Different tone per persona
- Evidence citations (if enabled)
- Forecast data (if enabled)
- Data source transparency

### API Calls

Open browser DevTools > Network tab:

**When opening settings:**

- GET `/v1/coach/personas` (fetches 5 personas)
- GET `/v1/tenants/{id}/data-sources` (fetches available sources)

**When sending message:**

- POST `/v1/tenants/{id}/coach/chat` with body:

  ```json
  {
    "message": "Your question",
    "persona": "business_analyst",
    "data_sources": ["orders"],
    "include_evidence": true,
    "include_forecast": false
  }
  ```

---

## 🐛 Troubleshooting

### Settings button not appearing

- Refresh page
- Check console for errors
- Verify imports in Coach.tsx

### No personas loading

- Check backend is running on port 8000
- Test endpoint: `curl http://localhost:8000/v1/coach/personas`
- Check browser console for API errors

### Data sources empty

- Verify tenant has data
- Check endpoint: `curl http://localhost:8000/v1/tenants/{id}/data-sources`
- Make sure connector data exists

### File upload not working

- File upload UI works (shows in list)
- Backend integration pending (Phase 2)
- Files are stored in local state only

---

## 📊 Expected Behavior

### Persona Changes Response Style

**Same Question, Different Personas:**

**Question:** "How's my revenue?"

**Business Analyst 📊:**

```
Revenue Analysis

Last 30 days: $45,230
• ↑ 12.3% vs previous period
• Orders: 523 (+8%)
• AOV: $86.47

Key Trends:
- Upward momentum
- Consistent order volume
```

**Data Scientist 🔬:**

```
Revenue Statistical Analysis

Period: Last 30 days
Mean: $45,230 (σ = $2,340)
Distribution: Normal (p < 0.05)

Forecast (95% CI):
Next 30d: $48,450 [$44,200 - $52,700]
Model: Holt-Winters (MAPE: 4.2%)
```

**Growth Strategist 🚀:**

```
Revenue Growth Opportunity

Current: $45,230/month
Target: $60,000/month (+33%)

Growth Levers:
1. Increase AOV: +$7K
2. Improve conversion: +$12K
3. Customer retention: +$9K

Quick wins in next 30 days! 🚀
```

### Data Source Filtering Works

**All Sources Selected:**

- Response includes: orders, inventory, customers
- More comprehensive insights

**Only "Orders" Selected:**

- Response focuses on: revenue, transactions
- Ignores inventory and customer data

**Only "Inventory" Selected:**

- Response focuses on: stock levels, turnover
- Ignores orders and customers

---

## ✅ Success Criteria

- [ ] Settings modal opens smoothly
- [ ] All 5 personas visible and selectable
- [ ] Selected persona shows in header
- [ ] Data sources checkable/uncheckable
- [ ] Source count badge updates
- [ ] File upload button works
- [ ] Evidence toggle changes responses
- [ ] Forecast toggle adds predictions
- [ ] Different personas give different tone
- [ ] API calls include new parameters

---

## 🎉 Demo Flow

### Full Demo (5 minutes)

1. **Open coach page**
   - Point out header layout

2. **Click settings ⚙️**
   - Walk through all 5 sections
   - Show persona descriptions
   - Show data source options

3. **Select Data Scientist 🔬**
   - Show active badge appears
   - Close modal
   - Point out header update

4. **Ask: "What will revenue be next month?"**
   - Show scientific, statistical response
   - Point out forecast data
   - Show evidence citations

5. **Switch to Growth Strategist 🚀**
   - Ask same question
   - Compare different response style

6. **Filter to only "Orders" data**
   - Show source count badge
   - Ask question
   - Note focused response

7. **Enable/disable evidence**
   - Show difference in response format

---

## 📝 Notes

- Backend is fully implemented ✅
- Frontend is fully implemented ✅
- All API endpoints working ✅
- File upload UI works ✅
- File upload backend = Phase 2 ⏳
- Evidence display = works if backend provides it
- Forecast integration = works if backend provides it

**You now have a GitHub Copilot-style settings interface for your Business Coach!** 🎉
