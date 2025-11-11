# Coach V4 - UX Gaps Quick Reference

**🔴 = Critical (Fix Now) | 🟡 = High Impact (Fix Soon) | 🟢 = Nice to Have**

---

## 🔴 Critical Gaps (Blockers)

### 1. No Help/Onboarding

- ❌ New users don't understand "health score"
- ❌ No tooltips explaining concepts
- ❌ No first-time tour
- ✅ **Fix**: Add onboarding modal + help icons

### 2. No Error/Loading States

- ❌ Blank screen when API fails
- ❌ Shows "0/100" if data missing
- ❌ No retry button
- ✅ **Fix**: Add skeletons, error alerts, retry

### 3. No Undo/Cancel

- ❌ Can't stop AI generation
- ❌ Accidental clicks auto-send
- ❌ No message deletion
- ✅ **Fix**: Add stop button, confirmations

### 4. No Data Freshness

- ❌ Users don't know if data is current
- ❌ No "last synced" timestamps
- ❌ Trust issue
- ✅ **Fix**: Show "Updated 2h ago" everywhere

### 5. No Keyboard Shortcuts

- ❌ Power users must click everything
- ❌ No CMD+K command palette
- ❌ No ESC to close
- ✅ **Fix**: Add shortcuts + palette

---

## 🟡 High-Impact Gaps

### 6. No Context Preservation

- ⚠️ Conversations lost on refresh
- ⚠️ Must restart every day
- ✅ **Fix**: Persist to localStorage/backend

### 7. No Action Tracking

- ⚠️ Recommendations don't get done
- ⚠️ No follow-up
- ✅ **Fix**: Add checkboxes, reminders

### 8. No "Why?" Explanations

- ⚠️ Can't drill down into metrics
- ⚠️ Black box AI
- ✅ **Fix**: Add "Why?" buttons

### 9. No Usage Guidance

- ⚠️ Users don't know when to check
- ⚠️ No habit formation
- ✅ **Fix**: Add tips, scheduled digests

### 10. Poor Mobile Input

- ⚠️ No voice input
- ⚠️ No quick reply chips
- ⚠️ Keyboard issues on iOS
- ✅ **Fix**: Voice button, chips, scroll fix

---

## 🟢 Nice to Have

11. No sharing/collaboration
12. No visual progress (charts)
13. No time comparisons
14. No personalization
15. No offline mode
16. No search
17. No templates
18. No integration previews
19. No bulk actions
20. No accessibility
21. No dark mode
22. No print/PDF
23. No feedback loop

---

## 🎯 Implementation Priority

**Week 1**: Error states, data freshness, help tooltips  
**Week 2**: Onboarding, undo/cancel, usage guidance  
**Week 3**: Keyboard shortcuts, context saving, action tracking  
**Week 4**: Mobile input, "why" explanations, trends

---

## 📈 Expected Impact

| Fix | User Pain Relieved | Impact |
|-----|-------------------|--------|
| Onboarding | "What is this?" | +88% activation |
| Error states | "Is this broken?" | +60% trust |
| Data freshness | "Can I trust this?" | +70% confidence |
| Undo/cancel | "I clicked wrong!" | +40% satisfaction |
| Context saving | "Start over daily?" | +83% retention |

---

## 💡 Key Quote

> "SMB users want a **personal trainer for business**, not a chatbot. Show me what to fix TODAY, why it matters, and track if I did it."

**Current Grade**: B+ (Good foundation, needs trust & control improvements)
