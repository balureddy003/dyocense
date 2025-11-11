# Business Coach V2 - Simplified Narrative Design

## 🎯 Design Philosophy

The new CoachV2 is designed for **SMB users who need clarity, not complexity**:

### Key Improvements

1. **📱 Clean, Full-Screen Chat**
   - No clutter - just conversation
   - Professional chat UI using @chatscope/chat-ui-kit-react (1.3k⭐, MIT license)
   - Natural conversation flow with proper message styling

2. **🎨 Floating Quick Actions**
   - Smart, context-aware suggestions
   - Based on actual business state (health score, tasks, goals)
   - Disappears after first interaction to keep focus on conversation

3. **📊 Collapsible Context Sidebar**
   - Business context available when needed
   - Quick navigation to Goals, Tasks
   - Data source indicators
   - Hidden by default to maximize chat space

4. **📋 Plan Inspector Drawer**
   - Full plan analysis moved to slide-out drawer
   - Shows actions, KPIs, evidence when needed
   - Keeps main chat uncluttered

5. **🔗 Connected Narratives**
   - Click icons to jump to Goals/Tasks pages
   - Seamless flow between coach and other features
   - Context-aware quick actions reference real data

## 🛠️ Tech Stack

### Frontend (Free & Popular)

- **@chatscope/chat-ui-kit-react** - Professional chat UI (1.3k⭐, MIT)
- **Mantine UI** - Modern component library
- **React Router** - Navigation

### Backend (Free & Popular)

- **LangChain** - AI orchestration (139k⭐, MIT) ✅ Already installed
- **LangGraph** - Multi-agent workflows ✅ Already installed
- **FastAPI** - Python backend

## 📂 File Structure

```
apps/smb/src/
├── pages/
│   ├── Coach.tsx          # Original (kept as /coach-old)
│   └── CoachV2.tsx        # New simplified version (now /coach)
├── components/
│   ├── AgentSelector.tsx  # Agent picker (reused)
│   ├── PlanSidebar.tsx    # Plan inspector (now in drawer)
│   └── ...
```

## 🚀 Usage

### Access New Coach

- Navigate to `/coach` - Shows new simplified CoachV2
- Navigate to `/coach-old` - Shows original version (for comparison)

### Features

**Quick Actions** (auto-generated based on business state):

- 🚨 Fix Health Issues (if score < 70)
- ✅ Prioritize Tasks (if tasks exist)
- 📊 Analyze Performance
- 🎯 Review/Set Goals
- 🚀 Growth Strategy

**Context Bar** (collapsible):

- Business name & health score
- Active goals count (click to navigate)
- Pending tasks count (click to navigate)
- Connected data sources

**Plan Inspector** (drawer):

- Overview & cost estimate
- Action items with numbering
- KPI snapshot
- Evidence sources
- Version control

## 🎨 UX Principles

1. **Progressive Disclosure**: Show complexity only when needed
2. **One Thing at a Time**: Focus on conversation, hide distractions
3. **Context-Aware**: Smart defaults based on actual business data
4. **Connected**: Easy navigation to related features
5. **Accessible**: Large touch targets, clear hierarchy

## 🔧 Customization

### Change Quick Actions

Edit `quickActions` array in `CoachV2.tsx` (lines ~121-160)

### Modify Chat Styling

chatscope styles imported from: `@chatscope/chat-ui-kit-styles/dist/default/styles.min.css`

Customize in your own CSS by overriding chatscope classes.

### Add New Agents

Update `agentConversations` initial state (lines ~68-108)

## 🌟 Benefits vs Original

| Feature | Original Coach | CoachV2 |
|---------|---------------|---------|
| Layout | 3-column cluttered | Full-width clean |
| Quick Actions | Static | Context-aware |
| Context | Always visible | Collapsible |
| Plan Inspector | Fixed column | Drawer |
| Navigation | Isolated | Connected |
| Chat UI | Custom | Professional (chatscope) |
| Mobile-friendly | ❌ | ✅ |
| SMB-focused | Complex | Simple |

## 🧪 Testing

1. Start dev server: `npm run dev`
2. Navigate to `/coach`
3. Try:
   - Toggle Context sidebar
   - Click quick actions
   - Send messages
   - Open Plan Inspector
   - Click Goal/Task icons to navigate

## 🔮 Future Enhancements

- [ ] Voice input support
- [ ] File attachments in chat
- [ ] Suggested follow-ups after each response
- [ ] Chat history sidebar
- [ ] Export conversation as PDF
- [ ] Multi-language support
- [ ] Dark mode

## 📝 Migration Path

Current users automatically get CoachV2 at `/coach`.

Original version accessible at `/coach-old` for reference.

No data migration needed - localStorage keys unchanged.
