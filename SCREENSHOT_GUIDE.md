# Business Fitness Dashboard - Screenshot Guide 📸

## What You'll See After Login

### 🏠 Home Dashboard (<http://localhost:5179/home>)

#### 1. **Header Section**

```
Business Fitness Dashboard
Welcome back, [Your Name] 👋
CycloneRake.com • Outdoor Equipment E-commerce
```

#### 2. **Business Health Score** (Large Ring - Apple Fitness Style)

```
┌────────────────────────────────────┐
│                                    │
│          ███████                   │
│       ███░░░░░░███                 │
│     ██░░░░░░░░░░░██               │
│    ██░░░░░░░░░░░░░██              │
│   ██░░░░░  78  ░░░░██             │
│   ██░░░░░Strong░░░░██             │
│    ██░░░░░░░░░░░░░██              │
│     ██░░░░░░░░░░██                │
│       ███░░░░███                   │
│          ███                       │
│                                    │
│   👍 Strong • ↑ +5% improvement   │
└────────────────────────────────────┘
```

#### 3. **Daily Snapshot** (4 Metric Cards in Row)

```
┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐
│ $12,450  │ │    47    │ │   94%    │ │   4.8    │
│ Revenue  │ │  Orders  │ │Fill Rate │ │ ★ Rating │
│ ↑ +8%    │ │ ↑ +12%   │ │ ↓ -2%    │ │ ↑ +3%    │
└──────────┘ └──────────┘ └──────────┘ └──────────┘
```

#### 4. **Active Goals** (Left Column)

```
ACTIVE GOALS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
┌─────────────────────────────────────┐
│ Seasonal Revenue Boost              │
│ 78,500 / 100,000 USD                │
│ [████████████████░░░░] 78% complete │
│                        23 days left │
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│ Inventory Optimization              │
│ 87 / 95 % Turnover                  │
│ [███████████████████░] 91% complete │
│                        30 days left │
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│ Customer Retention                  │
│ 142 / 200 Repeat Customers          │
│ [█████████████░░░░░░] 71% complete  │
│                        15 days left │
└─────────────────────────────────────┘
```

#### 5. **This Week's Plan** (Left Column)

```
THIS WEEK'S PLAN                2/5 completed
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
┌──────────────────────────────────────┐
│ ✅ Review GrandNode abandoned carts  │
│    Sales                             │
│                                      │
│ ✅ Update Kennedy ERP inventory      │
│    Operations                        │
│                                      │
│ ☐  Analyze top-selling outdoor gear  │
│    Analytics                         │
│                                      │
│ ☐  Follow up with wholesale customers│
│    Sales                             │
│                                      │
│ ☐  Optimize product recommendations  │
│    Marketing                         │
└──────────────────────────────────────┘
```

#### 6. **AI Copilot** (Right Column)

```
✨ AI COPILOT              Powered by GPT-4
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
┌──────────────────────────────────────┐
│ ⚠️ 2 hours ago                       │
│ Cart abandonment rate is up 18% this │
│ week. Consider sending personalized  │
│ follow-up emails to recover sales.   │
└──────────────────────────────────────┘

┌──────────────────────────────────────┐
│ 💡 5 hours ago                       │
│ Your best-selling camping gear       │
│ (tents, sleeping bags) are running   │
│ low. Reorder from supplier to avoid  │
│ stockouts.                           │
└──────────────────────────────────────┘

┌──────────────────────────────────────┐
│ Ask AI copilot anything...           │
│                                 [➤]  │
└──────────────────────────────────────┘
```

## Color Coding Reference

### Health Score Ring

- **Teal** (90-100): Excellent 💪
- **Green** (75-89): Strong 👍
- **Blue** (60-74): Good ✓
- **Yellow** (40-59): Needs Attention ⚠️
- **Red** (0-39): Critical 🚨

### Trend Indicators

- **Green ↑**: Positive trend (improving)
- **Red ↓**: Negative trend (declining)
- **Gray →**: Stable (no significant change)

### Goal Progress Bars

- **Teal** (90-100%): Nearly complete
- **Green** (70-89%): On track
- **Blue** (50-69%): Making progress
- **Yellow** (<50%): Needs attention

### AI Insight Cards

- **Yellow Background** ⚠️: Alerts (requires immediate attention)
- **Blue Background** 💡: Suggestions (recommended actions)
- **Teal Background** ✨: Insights (data-driven observations)

## Mobile View (< 768px)

### Stacked Layout

```
┌────────────────────────┐
│ Header                 │
├────────────────────────┤
│ Health Score (Ring)    │
├────────────────────────┤
│ Revenue Card           │
├────────────────────────┤
│ Orders Card            │
├────────────────────────┤
│ Fill Rate Card         │
├────────────────────────┤
│ Rating Card            │
├────────────────────────┤
│ Active Goals           │
│ (3 cards stacked)      │
├────────────────────────┤
│ Weekly Plan            │
│ (checklist)            │
├────────────────────────┤
│ AI Copilot             │
│ (insights + chat)      │
└────────────────────────┘
```

## Desktop View (≥ 1024px)

### Two-Column Grid

```
┌────────────────────────────────────────┐
│ Header + Health Score                  │
├────────────────────────────────────────┤
│ Daily Snapshot (4 cards in row)        │
├──────────────────────┬─────────────────┤
│ Left Column:         │ Right Column:   │
│                      │                 │
│ • Active Goals       │ • AI Copilot    │
│   (3 cards)          │   (insights +   │
│                      │    chat input)  │
│ • Weekly Plan        │                 │
│   (checklist)        │                 │
│                      │                 │
└──────────────────────┴─────────────────┘
```

## Interactive Elements

### ✅ Clickable/Interactive

1. **Weekly Plan Checkboxes**: Click to toggle task completion
2. **AI Chat Input**: Type and press Enter (or click send button)
3. **Goal Cards**: Click to view details (future enhancement)
4. **Metric Cards**: Click to drill down into data (future enhancement)

### 📊 Data Updates (Mock → Real)

Currently showing **mock data** for demonstration:

- Health Score: 78 (will calculate from real metrics)
- Metrics: Static values (will pull from GrandNode + Salesforce)
- Goals: Pre-configured (will load from template)
- Tasks: Hardcoded (will generate from AI)
- Insights: Sample messages (will generate from GPT-4)

## Navigation

### Bottom Nav (Mobile)

```
┌────┬────┬────┬────┬────┐
│🏠  │📊  │✨  │🔌  │👤  │
│Home│Plan│Chat│Conn│Prof│
└────┴────┴────┴────┴────┘
```

### Top Nav (Desktop)

- Workspace badge with CycloneRake.com logo
- User profile menu (top right)

## Testing Checklist

### Visual Verification

- [ ] Health score ring displays 78 with "Strong" label
- [ ] All 4 metric cards show values and trend arrows
- [ ] 3 goal cards with progress bars visible
- [ ] 5 weekly tasks with checkboxes (2 checked, 3 unchecked)
- [ ] 2 AI insight cards with colored backgrounds
- [ ] Chat input with send button at bottom of AI copilot

### Interaction Testing

- [ ] Click checkbox on weekly task → strikethrough appears
- [ ] Complete all 5 tasks → see "🎉 Week complete!" message
- [ ] Type in AI chat input → send button enables
- [ ] Press Enter in chat input → message clears (mock)
- [ ] Resize browser → layout responds (mobile/desktop views)

### Responsive Testing

- [ ] Mobile (375px): All elements stack vertically
- [ ] Tablet (768px): Metrics stay in row, goals/plan stack
- [ ] Desktop (1024px): Two-column layout for goals + AI copilot
- [ ] Large desktop (1440px): Content centers, max-width container

## Troubleshooting

### Issue: Components Not Rendering

**Solution**: Check browser console for errors

```bash
# In browser: Open DevTools (F12) → Console tab
# Look for: Module import errors, undefined variables
```

### Issue: Mock Data Not Showing

**Solution**: Verify Home.tsx is loaded correctly

```typescript
// Check in Home.tsx:
const mockHealthScore = { score: 78, trend: 5 }
const mockMetrics = { revenue: { value: '$12,450', trend: 8 }, ... }
```

### Issue: Styling Looks Wrong

**Solution**: Check Tailwind CSS and Mantine are loaded

```bash
# In browser: Inspect element → Computed styles
# Should see: Inter font, neutral-50 backgrounds, rounded corners
```

### Issue: Icons Missing (AI Copilot)

**Solution**: Verify @tabler/icons-react is installed

```bash
cd apps/smb
npm list @tabler/icons-react
# Should show: @tabler/icons-react@<version>
```

## Next Steps for Real Data

1. **Connect GrandNode**:
   - API endpoint: `https://cyclonerake.com/api`
   - Pull: orders, products, customers, cart abandonment
   - Update: `mockMetrics` with real values

2. **Connect Salesforce Kennedy ERP**:
   - API endpoint: Salesforce REST API
   - Pull: inventory levels, supplier data, costs
   - Update: `mockHealthScore` calculation

3. **Implement Health Score Engine**:
   - File: `src/utils/calculateHealthScore.ts`
   - Formula: Revenue Growth 25% + Profit Margin 20% + Cash Flow 15% + ...
   - Replace: `mockHealthScore` with `calculateHealthScore(connectorData)`

4. **Build Template System**:
   - File: `src/templates/cyclonerake.json`
   - Load: Goals, metrics definitions, connector configs
   - Render: Dynamic dashboard based on template

---

**Ready to Test**: Navigate to <http://localhost:5179/home> (after login)
**Screenshot Tool**: Use browser DevTools → Device Toolbar to test mobile views
**Documentation**: See `BUSINESS_FITNESS_CONCEPT.md` for complete vision
