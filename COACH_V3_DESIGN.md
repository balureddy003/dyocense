# Coach UI V3 - Three-Panel Responsive Layout

## 🎯 Design Overview

Completely redesigned the Business Coach interface with a **professional three-panel layout** optimized for SMB users who need context, conversation, and actionable plans all in one view.

---

## 📐 Layout Structure

```
┌─────────────────────────────────────────────────────────────────┐
│  Header: Agent Selector | Quick Nav (Goals/Tasks)               │
├──────────────┬─────────────────────────┬────────────────────────┤
│              │                         │                        │
│   BUSINESS   │         CHAT           │     ACTION PLAN        │
│   CONTEXT    │       (Middle)          │       (Right)          │
│   (Left)     │                         │                        │
│              │                         │                        │
│  [Collapse▶] │    User Message         │  [◀Collapse]          │
│              │    AI Response          │                        │
│  Health      │    User Message         │  Latest Plan           │
│  Score       │    AI Response          │  Recommendations       │
│              │    ...                  │                        │
│  Goals       │                         │  Quick Questions       │
│  (3 shown)   │  ┌──────────────────┐  │  - Improve Health      │
│              │  │ Type message...  │  │  - Weekly Plan         │
│  Tasks       │  └──────────────────┘  │  - Revenue Tips        │
│  (5 shown)   │        [Send]           │                        │
│              │                         │                        │
│  Quick Nav   │                         │                        │
│              │                         │                        │
└──────────────┴─────────────────────────┴────────────────────────┘
```

---

## 🎨 Key Features

### 1. **Left Panel - Business Context (300px, Collapsible)**

Shows real-time business health and priorities:

**Health Score Card:**

- Current overall score (0-100) with color coding
  - Green (70+): Healthy
  - Yellow (50-69): Needs attention
  - Red (<50): Critical
- Breakdown by category:
  - 💰 Revenue health
  - ⚙️ Operations health
  - 👥 Customer health
- Visual progress bar

**Active Goals (Top 3):**

- Goal title with progress percentage
- Visual progress bar
- "View all X goals →" if more than 3
- Empty state: "No active goals. Create one"

**Pending Tasks (Top 5):**

- Bullet list of task titles
- Badge showing total count
- "View all X tasks →" if more than 5
- Empty state: "All caught up! 🎉"

**Quick Navigation:**

- Analytics button → /analytics
- Data Sources button → /connectors

**Collapse/Expand:**

- IconLayoutSidebarLeftCollapse → Minimizes to 40px vertical bar
- Click bar to expand back
- Remembers state during session

### 2. **Middle Panel - Chat Interface (Flexible Width)**

Primary conversation area:

**Chat Messages:**

- User messages: Blue bubbles, right-aligned (max 85% width)
- AI messages: White bubbles, left-aligned (max 85% width)
- Markdown rendering for AI responses:
  - **Bold**, *italic*, lists, code blocks
  - Headings (h1-h3) with proper sizing
  - Proper spacing and typography

**Typing Indicator:**

- "Thinking..." with animated dots
- Shows during API call

**Message Input:**

- Auto-sizing textarea (1-4 rows)
- Enter to send, Shift+Enter for new line
- Placeholder: "Ask your AI coach anything about your business..."
- Send button with icon (disabled when empty)

**Auto-scroll:**

- Automatically scrolls to latest message
- Smooth scroll behavior

### 3. **Right Panel - Action Plan (320px, Collapsible)**

Shows actionable recommendations:

**Latest Recommendations Card:**

- Displays last AI message containing action/plan/task keywords
- Markdown-rendered with compact styling
- Empty state: "Ask your coach for recommendations..."

**Quick Questions:**

- Pre-written prompts for common queries:
  - "Improve Health Score" (uses current score)
  - "Weekly Action Plan"
  - "Revenue Growth Tips"
  - "Review My Goals" (conditional, only if goals exist)
- One-click sends to coach

**Collapse/Expand:**

- IconLayoutSidebarRightCollapse → Minimizes to 40px vertical bar
- Click bar to expand back

---

## 💻 Technical Implementation

### **Tech Stack:**

- **Frontend:** React + TypeScript + Mantine UI
- **Backend:** LangChain (139k⭐) + LangGraph (already installed)
- **Markdown:** react-markdown + remark-gfm
- **State:** React hooks + localStorage for persistence
- **API:** REST endpoints for chat and business context

### **State Management:**

```typescript
// Panel visibility
const [leftPanelCollapsed, setLeftPanelCollapsed] = useState(false)
const [rightPanelCollapsed, setRightPanelCollapsed] = useState(false)

// Chat state
const [agentConversations, setAgentConversations] = useState<Record<string, Message[]>>({})
const [selectedPersona, setSelectedPersona] = useState('business_analyst')
const [input, setInput] = useState('')
const [isLoading, setIsLoading] = useState(false)

// Business context (React Query)
const { data: healthScore } = useQuery({ ... })
const { data: goalsData } = useQuery({ ... })
const { data: tasksData } = useQuery({ ... })
```

### **Responsive Behavior:**

- Left panel: 300px → 40px collapsed
- Right panel: 320px → 40px collapsed
- Middle panel: Flex 1 (takes remaining space)
- Minimum middle width maintained for readability

### **Keyboard Shortcuts:**

- Enter: Send message
- Shift+Enter: New line in message
- Auto-focus on input after send

### **Data Persistence:**

- Conversations saved to localStorage per tenant
- Keyed by: `agent-conversations-${tenantId}`
- Persists across page refreshes
- Separate history per agent persona

---

## 🎯 User Experience Improvements

### **Before (CoachV2):**

❌ Floating quick actions cluttered the view  
❌ Context sidebar was hidden by default  
❌ No clear view of action plans  
❌ Had to toggle drawers to see business metrics  
❌ Chat took full width, wasting space  

### **After (CoachV3):**

✅ **Always-visible business context** (unless manually collapsed)  
✅ **Chat optimized for conversation** with proper message widths  
✅ **Action plans visible** alongside chat  
✅ **One-click quick questions** in right panel  
✅ **Professional three-column layout** like Slack/Discord  
✅ **Collapsible panels** for focus mode  
✅ **Real-time health metrics** always in view  

---

## 🚀 Usage Scenarios

### **Scenario 1: First-time User**

1. Opens Coach page
2. Sees welcome message from Business Analyst
3. Left panel shows health score (likely 0 if no data)
4. Right panel suggests quick questions
5. User asks: "How do I improve my health score?"
6. AI responds with recommendations
7. Recommendations appear in right panel as action plan

### **Scenario 2: Existing User with Goals**

1. Opens Coach page
2. Left panel shows:
   - Health score: 65/100 (yellow)
   - 3 active goals with progress bars
   - 7 pending tasks
3. User sees quick question: "Review My Goals"
4. Clicks it → AI analyzes goal progress
5. Right panel shows actionable next steps
6. User can navigate to /goals to update progress

### **Scenario 3: Focus Mode**

1. User collapses both side panels
2. Chat expands to full width
3. User focuses on deep conversation
4. Can expand panels anytime with one click

### **Scenario 4: Multi-tasking**

1. User keeps all panels open
2. Chats with Growth Strategist about revenue
3. Simultaneously monitors health score in left panel
4. Sees action plan update in right panel
5. Clicks "View Analytics" to dive deeper

---

## 🔧 Configuration

### **Agent Personas:**

Each agent has a unique introduction explaining their fitness coaching role:

1. **Business Analyst** - Overall business fitness coach
2. **Data Scientist** - Analytics and forecasting coach
3. **Consultant** - Strategic fitness coach
4. **Operations Manager** - Efficiency coach
5. **Growth Strategist** - Revenue fitness coach

All emphasize the **"AI Fitness Coach for Business"** metaphor.

### **API Integration:**

```typescript
// Send message
POST /v1/tenants/:tenantId/coach/chat
{
  message: string,
  conversation_history: Message[],
  persona: string
}

// Response
{
  message: string,  // AI response (markdown)
  timestamp: string
}
```

### **LangChain/LangGraph Backend:**

Already installed in requirements-dev.txt:

```
langgraph==0.0.40
langchain==0.1.20
langchain-openai==0.1.6
langchain-core==0.1.53
langchain-community==0.0.38
langchain-text-splitters==0.0.2
```

Perfect for:

- Multi-agent orchestration
- Tool calling (connect to business APIs)
- Streaming responses
- Memory management
- Agent graphs for complex workflows

---

## 📊 Comparison with Other Chat UIs

| Feature | CoachV3 (Ours) | ChatGPT | Slack | Microsoft Teams |
|---------|----------------|---------|-------|-----------------|
| Business context panel | ✅ | ❌ | ❌ | ❌ |
| Action plan panel | ✅ | ❌ | ❌ | ❌ |
| Collapsible sidebars | ✅ | ❌ | ✅ | ✅ |
| Quick question buttons | ✅ | ✅ (suggested) | ❌ | ❌ |
| Real-time metrics | ✅ | ❌ | ❌ | ❌ |
| Markdown rendering | ✅ | ✅ | ✅ | ✅ |
| Multi-agent support | ✅ | ✅ (GPTs) | ❌ | ❌ |
| Business-specific | ✅ | ❌ | ❌ | ❌ |

---

## 🎨 Design Tokens

### **Colors:**

- Background: `#f1f3f5` (light gray)
- Panel background: `white`
- Border: `#dee2e6`
- Primary: `#6366f1` (indigo)
- User bubble: `#4c6ef5` (blue)
- AI bubble: `white`

### **Spacing:**

- Panel padding: `12-16px`
- Card padding: `md` (16px)
- Gap between cards: `md` (16px)
- Message gap: `md` (16px)

### **Typography:**

- Headers: Inter var, 600 weight
- Body: Inter var, 400 weight
- Code: Monospace
- Sizes: 10px (tiny) → 14px (base) → 16px (large)

### **Shadows:**

- Cards: `0 1px 3px rgba(0,0,0,0.1)`
- Messages: `0 2px 8px rgba(0,0,0,0.08)`
- None on panels (clean borders only)

---

## 📱 Future Enhancements

### **Phase 1 - Mobile Responsive:**

- [ ] Stack panels vertically on mobile
- [ ] Bottom sheet for context/plan
- [ ] Swipe gestures to switch panels
- [ ] Full-screen chat by default

### **Phase 2 - Advanced Features:**

- [ ] Voice input (speech-to-text)
- [ ] File attachments (CSV, images)
- [ ] Export conversation as PDF
- [ ] Share recommendations to team
- [ ] Scheduled coaching sessions

### **Phase 3 - AI Enhancements:**

- [ ] Streaming responses (word-by-word)
- [ ] Multi-modal (charts, graphs)
- [ ] Proactive suggestions
- [ ] Context-aware quick questions
- [ ] Agent collaboration (multi-agent)

---

## ✅ Testing Checklist

- [x] Left panel displays health score correctly
- [x] Left panel shows top 3 goals with progress
- [x] Left panel shows top 5 tasks
- [x] Left panel collapse/expand works
- [x] Middle panel renders user messages (blue, right)
- [x] Middle panel renders AI messages (white, left, markdown)
- [x] Middle panel auto-scrolls to latest message
- [x] Middle panel textarea auto-resizes (1-4 rows)
- [x] Middle panel Enter sends, Shift+Enter new line
- [x] Right panel shows latest AI plan
- [x] Right panel quick questions work
- [x] Right panel collapse/expand works
- [x] Agent selector changes persona
- [x] Conversations persist in localStorage
- [x] Separate history per agent
- [x] Typing indicator shows during loading
- [x] Error handling for failed API calls
- [x] Responsive layout (all panels visible)
- [x] Navigation buttons work (Goals, Tasks, Analytics, Data)

---

## 🏆 Summary

**CoachV3** transforms the business coach from a simple chat interface into a **comprehensive command center** for SMB owners. With always-visible business context, real-time metrics, and actionable plans alongside the conversation, users can make informed decisions without context-switching.

The three-panel layout is:

- **Intuitive**: Follows familiar patterns from Slack/Discord
- **Responsive**: Collapsible panels for focus mode
- **Business-focused**: Shows what matters (health, goals, tasks)
- **Action-oriented**: Quick questions and plans drive execution
- **Powered by LangChain**: Enterprise-grade AI framework

Perfect for SMB owners who need their business fitness coach to be both conversational AND contextually aware of their business health.
