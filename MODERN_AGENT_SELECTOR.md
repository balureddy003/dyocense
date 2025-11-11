# Modern Agent Selector - Copilot Style

## ✨ New Design Implementation

### Visual Layout

```
┌──────────────────────────────────────────────────────────┐
│                    CHAT MESSAGES                         │
│                                                          │
│  👤 You: How can I grow my revenue?                     │
│                                                          │
│  📊 Business Analyst:                                    │
│  Based on your data, here are key growth opportunities:  │
│  • Increase AOV by 15% through bundling                 │
│  • Improve conversion rate to 4.5%                      │
│                                                          │
└──────────────────────────────────────────────────────────┘
┌──────────────────────────────────────────────────────────┐
│ [📊 Business Analyst ▼]  [2 sources] [Evidence] [⚙️]   │ ← Agent selector
├──────────────────────────────────────────────────────────┤
│ 📎  @mention an agent or ask anything...          🎤 ⬆  │ ← Input with actions
└──────────────────────────────────────────────────────────┘
```

## 🎯 Key Features

### 1. **Sleek Agent Selector (Dark Theme)**

Click the agent button to see a dropdown with all available agents:

```
┌─────────────────────────────────────────┐
│ SELECT AGENT                            │
├─────────────────────────────────────────┤
│ 📊 Business Analyst             [Active]│ ← Current
│    Data-driven KPI analysis             │
├─────────────────────────────────────────┤
│ 🔬 Data Scientist                       │
│    Predictive analytics & forecasting   │
├─────────────────────────────────────────┤
│ 💼 Consultant                           │
│    Strategic planning & frameworks      │
├─────────────────────────────────────────┤
│ ⚙️ Operations Manager                   │
│    Process efficiency & optimization    │
├─────────────────────────────────────────┤
│ 🚀 Growth Strategist                    │
│    Revenue growth & scaling             │
└─────────────────────────────────────────┘
```

**Design Details:**

- Dark background (#1f2937)
- Icon with color-coded avatar
- Agent name + description
- Active state indicator (blue dot)
- Smooth hover animations
- One-click switching

### 2. **Clean Input Area**

Modern, minimalist design:

```
[📎] @mention an agent or ask anything...  [🎤] [⬆]
 │                                           │    └─ Send (blue)
 │                                           └───── Voice input
 └────────────────────────────────────────────── Attach files
```

**Features:**

- Borderless input (clean look)
- File attachment icon (left)
- Voice input icon (right)
- Send button (rounded, blue)
- Auto-expanding textarea
- @mention support (future)

### 3. **Status Badges**

Quick visual indicators:

```
[2 sources] [Evidence] [Forecast]
    │           │          └─ Blue dot (forecasting enabled)
    │           └─ Green dot (citations enabled)
    └─ Gray badge (data source count)
```

## 🎨 Color Scheme

### Agent Colors

Each agent has a unique color for quick recognition:

| Agent | Color | Hex |
|-------|-------|-----|
| 📊 Business Analyst | Blue | #3b82f6 |
| 🔬 Data Scientist | Purple | #8b5cf6 |
| 💼 Consultant | Cyan | #0ea5e9 |
| ⚙️ Operations Manager | Amber | #f59e0b |
| 🚀 Growth Strategist | Green | #10b981 |

### UI Elements

- Background: #374151 (dark gray)
- Hover: #4b5563 (lighter gray)
- Active: #374151 with blue accent
- Text: White (#ffffff)
- Dimmed text: #9ca3af

## 💡 User Interactions

### Switching Agents

**Method 1: Click Dropdown**

1. Click agent button
2. Dark dropdown appears
3. See all 5 agents with descriptions
4. Click desired agent
5. Dropdown closes, agent switches instantly
6. New agent icon shows in button

**Method 2: @Mention (Future)**

```
Type: @data scientist analyze my revenue
      └─ Auto-switches to Data Scientist
```

### Quick Settings Access

- Click ⚙️ icon → Full settings modal
- Modify data sources, evidence, forecast options
- All changes apply immediately

## 🔄 Comparison

### Before (Old Settings Bar)

```
┌────────────────────────────────────────┐
│ Coach: [📊 Business Analyst] • [2     │
│ sources]    [Citations] [Forecast] ⚙️  │
└────────────────────────────────────────┘
```

- Light background
- Multiple separate elements
- Less compact
- Harder to scan

### After (New Agent Selector)

```
┌────────────────────────────────────────┐
│ [📊 Business Analyst ▼] [2 sources]   │
│                    [Evidence] [⚙️]     │
└────────────────────────────────────────┘
```

- Dark, sleek dropdown
- Compact layout
- Easier agent switching
- More professional look

## 📱 Responsive Behavior

### Desktop

Full layout with all elements visible

### Tablet

Badges may wrap to second row

### Mobile

```
┌──────────────────────┐
│ [📊 Analyst ▼]   ⚙️  │
├──────────────────────┤
│ 📎  Ask...      🎤 ⬆ │
└──────────────────────┘
```

## 🎯 Benefits

✅ **Faster Switching** - One click, no modal needed
✅ **Visual Clarity** - Color-coded agents
✅ **Professional Look** - Dark theme dropdown
✅ **Compact Design** - More screen space for chat
✅ **Familiar Pattern** - GitHub Copilot style
✅ **Clear Feedback** - Active state always visible

## 🚀 Future Enhancements

### Phase 2: @Mentions

```
User types: @data scientist
            └─ Autocomplete appears
            
Options shown:
• @data scientist
• @business analyst
• @consultant
```

### Phase 3: Agent History

Show recently used agents at top of dropdown

### Phase 4: Custom Agents

Allow users to create and save custom agent configurations

## 📊 Usage Examples

### Example 1: Revenue Analysis

```
Selected: 📊 Business Analyst
Input: "How's my revenue this month?"
Response: KPI-focused, data-driven analysis
```

### Example 2: Forecasting

```
Click dropdown → Select 🔬 Data Scientist
Input: "What will revenue be next month?"
Response: Statistical forecast with confidence intervals
```

### Example 3: Strategy Planning

```
Switch to: 💼 Consultant
Input: "How should I grow my business?"
Response: Strategic framework and action plan
```

## 🎨 Implementation Details

### AgentSelector Component

- Located in: `/apps/smb/src/components/AgentSelector.tsx`
- Uses Mantine Popover for dropdown
- Custom styling for dark theme
- Smooth animations and transitions

### Coach Page Updates

- Replaced old settings bar
- Added file attachment icon
- Added voice input icon
- Borderless input styling
- Cleaner layout overall

### Agent Icons Mapping

```typescript
business_analyst → IconChartBar
data_scientist → IconBrain
consultant → IconBriefcase
operations_manager → IconTool
growth_strategist → IconRocket
```

## ✅ Testing Checklist

- [ ] Agent dropdown opens on click
- [ ] All 5 agents visible in dropdown
- [ ] Active agent highlighted
- [ ] Switching agents works instantly
- [ ] Dropdown closes after selection
- [ ] Button shows correct agent name/icon
- [ ] Status badges display correctly
- [ ] Settings icon opens modal
- [ ] Input accepts text normally
- [ ] Send button enables/disables properly
