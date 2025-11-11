# In-Chat Settings Bar - UI Layout

## New Design: Settings Inside Chat Window

### Before (Settings in Header)

```
┌─────────────────────────────────────────────────────┐
│ ✨ AI ASSISTANT              [2 sources] ⚙️         │ ← Settings here
│ Business Coach  [📊 Business Analyst]               │
│ Get personalized guidance...                        │
└─────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────┐
│                  CHAT MESSAGES                      │
│                                                     │
│                                                     │
│                                                     │
└─────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────┐
│ [Type your message...]                      [Send]  │
└─────────────────────────────────────────────────────┘
```

### After (Settings in Chat Window)

```
┌─────────────────────────────────────────────────────┐
│ ✨ AI ASSISTANT                                     │ ← Clean header
│ Business Coach                                      │
│ Get personalized guidance...                        │
└─────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────┐
│                  CHAT MESSAGES                      │
│                                                     │
│                                                     │
│                                                     │
└─────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────┐
│ Coach: [📊 Business Analyst ▾] • [2 sources]       │ ← Quick settings
│                         [Citations] [Forecast] ⚙️   │
├─────────────────────────────────────────────────────┤
│ [Type your message...]                      [Send]  │
└─────────────────────────────────────────────────────┘
```

## Detailed Settings Bar Layout

```
┌───────────────────────────────────────────────────────────────┐
│                        Chat Messages Area                     │
│                                                               │
└───────────────────────────────────────────────────────────────┘
┌───────────────────────────────────────────────────────────────┐
│ Coach: [📊 Business Analyst ▾]  •  [📊 2 sources]            │
│                              [Citations] [Forecast] ⚙️        │
├───────────────────────────────────────────────────────────────┤
│                                                               │
│  Ask me anything about your business...                       │
│                                                         [Send]│
│  Press Enter to send, Shift+Enter for new line               │
└───────────────────────────────────────────────────────────────┘
```

## Interactive Elements

### Left Side - Coach Selection

```
Coach: [📊 Business Analyst ▾]
       └─ Click to open settings modal
       
• [📊 2 sources]
  └─ Shows selected data sources count
```

### Right Side - Quick Indicators

```
[Citations]  ← Green dot badge (if enabled)
[Forecast]   ← Blue dot badge (if enabled)
⚙️           ← Settings icon (opens modal)
```

## Click Behaviors

1. **Click "Business Analyst" button**
   → Opens settings modal
   → Auto-focuses on persona selection

2. **Click "2 sources" badge**
   → Visual indicator of active filters
   → Click opens settings to modify

3. **Click Citations/Forecast badges**
   → Tooltips show "Evidence citations enabled"
   → Visual confirmation of active features

4. **Click ⚙️ icon**
   → Opens full settings modal
   → All options available

## Benefits

✅ **Quick Access** - Settings right where you type
✅ **Context Aware** - See active settings while chatting
✅ **No Scrolling** - Settings always visible at bottom
✅ **Clean Header** - More focus on content
✅ **GitHub Copilot Style** - Similar to familiar interfaces
✅ **One Click** - Fast persona switching

## Visual States

### Minimal (No customization)

```
┌───────────────────────────────────────────┐
│ Coach: [📊 Business Analyst ▾]      ⚙️   │
└───────────────────────────────────────────┘
```

### With Data Sources

```
┌───────────────────────────────────────────┐
│ Coach: [📊 Business Analyst ▾] • [2 ⚙️   │
│        sources]                           │
└───────────────────────────────────────────┘
```

### Fully Customized

```
┌────────────────────────────────────────────────┐
│ Coach: [🔬 Data Scientist ▾] • [3 sources]    │
│                    [Citations] [Forecast] ⚙️  │
└────────────────────────────────────────────────┘
```

## Color Scheme

- **Background**: #fafafa (light gray)
- **Border**: #e5e7eb (subtle gray)
- **Text**: Dimmed for labels
- **Badges**:
  - Citations: Green dot variant
  - Forecast: Blue dot variant
  - Data sources: Light variant with icon
- **Button**: Light variant, clickable

## Responsive Behavior

### Desktop (>768px)

```
┌─────────────────────────────────────────────────────┐
│ Coach: [📊 Business Analyst ▾] • [2 sources]       │
│                         [Citations] [Forecast] ⚙️   │
└─────────────────────────────────────────────────────┘
```

### Mobile (<768px)

```
┌──────────────────────────────────┐
│ [📊 Business Analyst ▾]      ⚙️  │
│ [2 sources] [Citations]          │
└──────────────────────────────────┘
```

## Implementation Details

### Component Structure

```tsx
<div className="quick-settings-bar">
  <Group justify="space-between">
    <Group gap="xs">
      {/* Left: Coach selector */}
      <Text>Coach:</Text>
      <Button onClick={openSettings}>
        {emoji} {name}
      </Button>
      
      {/* Data sources indicator */}
      {sources.length > 0 && (
        <Badge>{sources.length} sources</Badge>
      )}
    </Group>
    
    <Group gap={4}>
      {/* Right: Feature badges */}
      {evidence && <Badge>Citations</Badge>}
      {forecast && <Badge>Forecast</Badge>}
      <ActionIcon onClick={openSettings}>⚙️</ActionIcon>
    </Group>
  </Group>
</div>
```

### Styling

- Padding: 12px 16px
- Background: #fafafa
- Border-top: 1px solid #e5e7eb
- Position: Between messages and input
- Height: Auto (adapts to content)

## User Experience Flow

1. **User opens coach** → Settings bar visible immediately
2. **Click coach name** → Modal opens to persona grid
3. **Select new persona** → Button updates instantly
4. **Badge shows status** → Clear visual feedback
5. **Type question** → Settings remain visible
6. **Response arrives** → Styled per selected persona

## Comparison with Competitors

### ChatGPT

- Settings in top-right hamburger menu
- Requires navigation away from chat
- No quick switching

### GitHub Copilot

- Settings icon in chat interface ✓ (We match this!)
- Model selector in dropdown
- Quick access to preferences

### Claude

- Settings in sidebar
- No inline switching
- Must leave chat context

### Our Solution

- ✅ Inline settings bar
- ✅ One-click persona switch
- ✅ Visual status indicators
- ✅ No context switching
- ✅ Always accessible
