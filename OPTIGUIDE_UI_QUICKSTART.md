# OptiGuide UI - Quick Start Guide

## What You Can Do Now

### 🎯 What-If Analysis

Ask scenario questions and see the impact on costs and inventory:

**Example Questions:**

- "What if order costs increase by 20%?"
- "What if holding costs double?"
- "What if we reduce safety stock by 30%?"
- "What if service level increases to 98%?"

**What You Get:**

- Original optimization results
- Modified optimization results  
- Cost comparison (before/after)
- Per-SKU impact breakdown
- Business-friendly recommendations

### 🔍 Why Analysis

Get root cause explanations for inventory issues:

**Example Questions:**

- "Why are inventory costs high?"
- "Why is WIDGET-001 overstocked?"
- "Why do we have excess inventory?"
- "Why are stockout risks increasing?"

**What You Get:**

- Clear root cause explanation
- Supporting evidence from optimization data
- Actionable recommendations
- Context-aware narratives

## How to Use

### Step 1: Open OptiGuide

1. Navigate to the Coach page in the SMB app
2. Look for the **"OptiGuide"** button in the top-right header (purple/violet color)
3. Click the button to open the OptiGuide drawer

### Step 2: Choose Analysis Mode

- **What-If Scenarios**: For scenario planning and cost impact
- **Why Analysis**: For root cause explanations

### Step 3: Ask a Question

**Option A - Use Examples:**

- Click one of the pre-built example buttons
- Examples auto-fill the question field

**Option B - Custom Question:**

- Type your question in the textarea
- Use natural language (e.g., "What if costs go up 15%?")

### Step 4: Run Analysis

1. Click the **"Run Analysis"** button
2. Wait 500-800ms for results (loading spinner shows progress)
3. View the rich narrative with visualizations

### Step 5: Interpret Results

**For What-If Analysis:**

```
📊 Cost Impact Card
├─ Original Cost: $67.89
├─ Modified Cost: $81.47
└─ Change: +$13.58 (+20.0%) ↑

📦 SKU-Level Impact
├─ WIDGET-001: $5.33 → $6.40 (↑)
├─ GADGET-002: $7.22 → $8.66 (↑)
└─ TOOL-003: $9.65 → $11.58 (↑)

💡 Recommendation:
"This scenario increases costs by 20%. Consider 
negotiating with suppliers or sourcing alternatives."
```

**For Why Analysis:**

```
📋 Root Cause:
"WIDGET-001 is overstocked because current inventory 
(450 units) exceeds optimal levels (290 units)"

💰 Impact:
"Leading to $5.33 in excess holding costs annually"

✅ Action:
"Reduce stock to 290 units through sales promotions 
or reduced ordering"
```

## UI Components

### OptiGuide Drawer

- **Location**: Slides in from right side
- **Size**: Extra-large (xl) for comfortable reading
- **Closable**: Click X or click outside drawer

### Mode Selector

- **What-If Scenarios** (default)
- **Why Analysis**
- Toggle between modes to switch question types

### Question Input

- **Textarea**: Multi-line input for questions
- **Placeholder**: Shows example question format
- **Disabled**: When analysis is running

### Example Buttons

- **4 examples per mode**: Quick access to common scenarios
- **One-click**: Auto-fills question field
- **Light variant**: Visual distinction from primary action

### Run Analysis Button

- **Full width**: Easy to find and click
- **Loading state**: Shows spinner when processing
- **Disabled**: When question is empty or analyzing

### Result Display

- **Narrative Card**: Main explanation with markdown
- **Cost Comparison**: Side-by-side metrics
- **SKU Breakdown**: Per-product impact list
- **Scenario Parameters**: Applied modifications in badges

## Tips & Best Practices

### ✅ Do's

- Start with example questions to understand capabilities
- Use specific numbers in what-if questions ("20%" vs "a lot")
- Ask one scenario at a time for clarity
- Review SKU-level details for actionable insights
- Try multiple scenarios to find optimal strategy

### ❌ Don'ts

- Don't ask multiple questions in one query
- Don't expect real-time streaming (results appear all at once)
- Don't use very complex multi-constraint scenarios (limited pattern matching)
- Don't close drawer while analysis is running

## Keyboard Shortcuts

- **Esc**: Close OptiGuide drawer
- **Tab**: Navigate between buttons
- **Enter**: Submit question (when focused in textarea)

## Error Messages

**"No tenant ID"**: User not logged in or session expired

- Solution: Refresh page or log in again

**"Failed to parse question"**: Pattern not recognized

- Solution: Use example format or simpler phrasing

**"Optimization failed"**: Backend solver issue

- Solution: Check if data is uploaded, retry request

**Network error**: Backend not responding

- Solution: Verify backend is running on port 8001

## Component Architecture

```
CoachV2 Page
└── OptiGuide Drawer
    └── OptiGuideQuickActions
        ├── Mode Selector (What-If / Why)
        ├── Question Input (Textarea)
        ├── Example Buttons
        ├── Run Analysis Button
        └── Result Display
            └── OptiGuideNarrative
                ├── Markdown Narrative
                ├── Cost Comparison Card
                ├── SKU Impact List
                └── Technical Analysis
```

## Next Steps

### For Users

1. **Explore Examples**: Click through all 8 pre-built questions
2. **Custom Scenarios**: Try your own business questions
3. **Compare Results**: Run multiple what-ifs to compare outcomes
4. **Take Action**: Use recommendations to make inventory decisions

### For Developers

1. **Add Charts**: Visualize cost trends with Recharts
2. **Scenario History**: Save and compare past analyses
3. **Export**: Add PDF export for narratives
4. **LLM Integration**: Connect OpenAI for advanced NLP

## Troubleshooting

**Issue**: OptiGuide button doesn't appear

- **Check**: Verify frontend built correctly (`npm run dev`)
- **Check**: Refresh browser cache

**Issue**: Drawer opens but shows error

- **Check**: Backend running on port 8001
- **Check**: Network tab for API call status
- **Run**: `curl http://localhost:8001/v1/capabilities`

**Issue**: Results take too long

- **Expected**: 500-800ms for basic scenarios
- **Check**: Backend logs for optimization errors
- **Try**: Simpler scenario with fewer SKUs

**Issue**: Narrative doesn't format correctly

- **Check**: Browser console for React errors
- **Check**: Markdown syntax in backend response

## API Endpoints Used

1. **POST /v1/tenants/{id}/what-if**
   - Request: `{ question, llm_config? }`
   - Response: WhatIfAnalysisResponse with before/after results

2. **POST /v1/tenants/{id}/why**
   - Request: `{ question, llm_config? }`
   - Response: WhyAnalysisResponse with root cause narrative

3. **GET /v1/capabilities**
   - Response: OptiGuide availability flags

## Browser Compatibility

- ✅ Chrome 90+
- ✅ Firefox 88+
- ✅ Safari 14+
- ✅ Edge 90+

Requires:

- ES6+ JavaScript support
- CSS Grid and Flexbox
- Fetch API
- Async/await

## Performance

- **Initial Load**: < 100ms (component mount)
- **What-If Analysis**: 500-800ms (without LLM)
- **Why Analysis**: 300-500ms (without LLM)
- **With LLM**: +1-3 seconds (OpenAI API latency)

## Support

For issues or questions:

1. Check backend logs: `/tmp/dyocense-backend.log`
2. Check browser console for frontend errors
3. Review `OPTIGUIDE_INTEGRATION.md` for backend details
4. Test backend directly: `./scripts/test_optiguide.sh`
