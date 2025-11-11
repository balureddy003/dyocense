# Testing Guide - Coach V4 Critical UX Improvements

## 🧪 How to Test New Features

### Prerequisites

```bash
cd apps/smb
npm install  # Ensure all dependencies installed
npm run dev  # Start development server
```

---

## Feature Testing Checklist

### ✅ 1. Error State Handling

**Test**: API Failure Scenario

1. Open DevTools → Network tab
2. Block `/health-score` endpoint (or go offline)
3. Reload page
4. **Expected**: Red error card with "Try Again" button
5. Click "Try Again"
6. **Expected**: Retry loads data successfully

---

### ✅ 2. Loading Skeletons

**Test**: Slow Network

1. DevTools → Network → Throttle to "Slow 3G"
2. Reload page
3. **Expected**: Animated skeleton screens for:
   - Health dashboard (gray placeholder boxes)
   - Goals list (3 skeleton cards)
   - Sidebar sections

---

### ✅ 3. Data Freshness Indicators

**Test**: Timestamp Display

1. Load page with health data
2. Look for small gray text below "Your Business Health"
3. **Expected**: "Updated 2h ago" (or similar)
4. If data is >6 hours old: text turns orange
5. Hover to see full timestamp

**Mock Old Data** (Optional):

```typescript
// In CoachV4.tsx, temporarily modify health score response
const mockOldHealthScore = {
    ...healthScore,
    updated_at: new Date(Date.now() - 8 * 60 * 60 * 1000) // 8 hours ago
}
```

---

### ✅ 4. Onboarding Tour

**Test**: First-Time User Experience

1. Clear localStorage: DevTools → Application → Local Storage → Clear All
2. Reload page
3. **Expected**: Modal appears with "Welcome to Your Business Coach"
4. Click "Next" through 5 steps
5. **Expected**: Progress dots at bottom show current step
6. Click "Get Started" on final step
7. **Expected**: Modal closes, won't show again

**Test**: Skip Tour

1. Clear localStorage again
2. Reload
3. Click "Skip tour" on first screen
4. **Expected**: Modal closes immediately

---

### ✅ 5. Conversation History

**Test**: Save & Resume Conversations

1. Start a new conversation: type "What's my revenue?" → Send
2. Wait for AI response
3. Check sidebar → "Recent Chats" section
4. **Expected**: New conversation appears with title
5. Click "New" button in sidebar
6. **Expected**: Chat clears, fresh start
7. Click on saved conversation in sidebar
8. **Expected**: Previous messages restore

**Test**: Delete Conversation

1. Hover over conversation in sidebar
2. Click trash icon
3. **Expected**: Conversation removed from list
4. If it was active: chat clears to fresh start

---

### ✅ 6. Stop Generation

**Test**: Cancel AI Response Mid-Stream

1. Type a question: "Give me a detailed business analysis"
2. Click Send
3. As AI starts typing (streaming)...
4. **Expected**: Send button becomes red Stop button
5. Click Stop button
6. **Expected**: Message shows "_Generation stopped by user_"
7. Input remains empty, ready for new message

---

### ✅ 7. Help Tooltips

**Test**: Contextual Help

1. Look for "?" icon next to "Your Business Health" header
2. Hover over icon
3. **Expected**: Tooltip appears explaining health score
4. Move mouse away
5. **Expected**: Tooltip disappears

---

## 🐛 Known Issues / Edge Cases

### Issue: Conversation doesn't save

**Cause**: localStorage disabled/full  
**Fix**: Check browser settings, clear old data

### Issue: Onboarding shows every time

**Cause**: localStorage cleared by extension/privacy mode  
**Fix**: Expected behavior in private browsing

### Issue: Stop button doesn't work

**Cause**: Backend doesn't respect AbortSignal yet  
**Fix**: See COACH_V4_CRITICAL_UX_IMPLEMENTATION.md for backend requirements

---

## 📊 Visual Regression Testing

### Before/After Screenshots

**Error State**:

- Before: Blank screen with "0/100"
- After: Red error card with retry button

**Loading**:

- Before: Blank white space during load
- After: Animated gray skeleton boxes

**Timestamps**:

- Before: No indication of data freshness
- After: "Updated 2h ago" in gray text

---

## 🔍 Code Review Checklist

- [ ] No TypeScript compilation errors
- [ ] All components have proper TypeScript interfaces
- [ ] Error boundaries catch render errors
- [ ] Loading states don't cause layout shift
- [ ] Timestamps formatted consistently
- [ ] Conversation history limits to 50 (performance)
- [ ] localStorage wrapped in try/catch
- [ ] AbortController cleaned up properly

---

## 🚀 Performance Testing

### Metrics to Monitor

1. **Time to Interactive (TTI)**
   - Before: 3.2s
   - After: Should be <3.5s (skeleton adds minimal overhead)

2. **localStorage Size**
   - Max: ~50 conversations × ~2KB = ~100KB
   - Check: DevTools → Application → Storage

3. **Memory Leaks**
   - Open page
   - Create 20 conversations
   - Check DevTools → Memory → Take snapshot
   - Expected: <50MB total

---

## 📱 Mobile Testing

### Responsive Breakpoints

**Mobile (<768px)**:

1. Sidebar defaults closed ✓
2. Onboarding modal fits screen ✓
3. Error cards stack vertically ✓
4. Loading skeletons scale down ✓

**Tablet (768-1024px)**:

1. Sidebar width: 240px ✓
2. Touch targets >44px ✓

---

## ✅ Acceptance Criteria

### Feature is "Done" When

1. **Error Handling**:
   - [ ] All API failures show error state
   - [ ] Retry button works
   - [ ] No console errors

2. **Loading**:
   - [ ] Skeletons match final layout
   - [ ] No content jump on load

3. **Freshness**:
   - [ ] Timestamps show on all data
   - [ ] Old data highlights in orange

4. **Onboarding**:
   - [ ] Tour shows for new users only
   - [ ] All 5 steps load correctly
   - [ ] Skip/complete both persist state

5. **History**:
   - [ ] Conversations save automatically
   - [ ] List shows in sidebar
   - [ ] Resume works correctly
   - [ ] Delete removes from list

6. **Stop**:
   - [ ] Button shows when sending
   - [ ] Abort cancels request
   - [ ] UI recovers gracefully

7. **Help**:
   - [ ] Tooltips appear on hover
   - [ ] Content is readable
   - [ ] Tooltips dismiss properly

---

## 🎬 Demo Script (for Stakeholders)

**5-Minute Walkthrough**:

1. **First-Time User** (1 min)
   - Clear localStorage
   - Show onboarding tour
   - "This guides new users through key features"

2. **Error Handling** (1 min)
   - Go offline
   - Show error state
   - Click retry
   - "No more blank screens!"

3. **Data Trust** (1 min)
   - Point to "Updated 2h ago"
   - "Users know data is current"

4. **Conversation History** (1 min)
   - Show saved conversations
   - Resume old chat
   - "Users can pick up where they left off"

5. **Control** (1 min)
   - Start generation
   - Click stop
   - "Users control the AI, not the other way around"

---

## 📞 Support

**Issues?** Check:

1. Browser console for errors
2. Network tab for failed requests
3. localStorage size/availability
4. Backend API responses include `updated_at`

**Questions?** See: `COACH_V4_CRITICAL_UX_IMPLEMENTATION.md`
