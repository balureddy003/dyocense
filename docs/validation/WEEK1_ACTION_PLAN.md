# Week 1 Action Plan - Validation Sprint

**Sprint Start Date:** November 13, 2025  
**Sprint Goal:** Create prototype and recruit 10 SMB owners for testing

---

## Monday, November 13 (TODAY)

### Morning: Leadership Kickoff

**9:00 AM - Leadership Decision Meeting (30 min)**

**Attendees:** CEO, CTO, Product Lead, Design Lead, CFO

**Agenda:**

1. Review consulting recommendations (5 min)
2. Review validation plan and budget (10 min)
3. Discuss resource allocation (5 min)
4. **DECISION:** Approve validation sprint? (5 min)
5. Next steps if approved (5 min)

**Required Decisions:**

- [ ] Approve $7,500 validation budget
- [ ] Assign Product Designer (full-time, Week 1-2)
- [ ] Assign Product Manager to coordinate
- [ ] Commit to Phase 1 if validation succeeds

**Action Items from Meeting:**

- [ ] Send approval email to team
- [ ] Create Slack channel: #coach-v6-validation
- [ ] Update company calendar with key milestones

---

### Late Morning: Team Kickoff (If Approved)

**10:30 AM - Validation Sprint Kickoff (60 min)**

**Attendees:** Product Designer, Product Manager, Engineering Lead, UX Researcher (if available)

**Agenda:**

1. Review strategic context (10 min)
   - Why we're doing this
   - What we're validating
   - Success criteria

2. Review documents (15 min)
   - Design spec: `COACH_V6_FITNESS_DASHBOARD_DESIGN_SPEC.md`
   - User testing script: `USER_TESTING_SCRIPT.md`
   - Recruitment materials: `RECRUITMENT_MATERIALS.md`

3. Assign responsibilities (10 min)
   - Designer: Figma mockups
   - PM: Recruitment + scheduling
   - Engineering: Technical feasibility

4. Timeline review (10 min)
   - What's due when
   - Dependencies
   - Checkpoints

5. Questions & risks (15 min)

**Action Items from Meeting:**

- [ ] Everyone: Read all validation docs
- [ ] Designer: Set up Figma file
- [ ] PM: Set up recruitment survey
- [ ] Engineering: Review implementation roadmap

---

### Afternoon: Get Started

**Product Designer Tasks:**

**2:00 PM - Set up Figma project (30 min)**

- [ ] Create new Figma file: "Coach V6 - Fitness Dashboard"
- [ ] Set up design system (colors, spacing, typography)
- [ ] Import Mantine component library
- [ ] Create artboards for 5 screens:
  - Home (Fitness Dashboard)
  - Health Score Detail
  - Coach Recommendation Detail
  - Current Chat UI (for comparison)
  - Mobile version

**2:30 PM - Start hero component (90 min)**

- [ ] Design health score header (3 states: good/warning/critical)
- [ ] Design "Needs Attention" / "Doing Well" cards
- [ ] Add sample data (realistic numbers)
- [ ] Create hover states

**4:00 PM - Review with PM (15 min)**

- [ ] Show progress
- [ ] Get feedback
- [ ] Align on priorities for Tuesday

---

**Product Manager Tasks:**

**2:00 PM - Set up recruitment (60 min)**

- [ ] Create Google Form with screener questions
- [ ] Set up email: <research@dyocense.com> (or use existing)
- [ ] Prepare $1,000 Amazon gift card balance
- [ ] Create tracking spreadsheet

**3:00 PM - Post recruitment ads (60 min)**

- [ ] Reddit r/smallbusiness (post recruitment thread)
- [ ] LinkedIn (personal + company account)
- [ ] Local business Facebook groups (if applicable)
- [ ] Email to existing users (if database available)

**4:00 PM - Set up scheduling (30 min)**

- [ ] Block calendar: Nov 18-22, 10am/2pm slots
- [ ] Create Zoom meeting links (or recurring link)
- [ ] Prepare confirmation email template
- [ ] Set up Calendly (optional, for self-scheduling)

**4:30 PM - Review with Designer (15 min)**

- [ ] See design progress
- [ ] Discuss what data to include in prototype
- [ ] Plan for tomorrow

---

**Engineering Lead Tasks:**

**2:00 PM - Technical review (120 min)**

- [ ] Read implementation roadmap carefully
- [ ] Review Phase 1 tasks and acceptance criteria
- [ ] Assess current CoachV5.tsx architecture
- [ ] Identify technical risks:
  - WebSocket infrastructure needed?
  - Caching strategy?
  - Health score calculation complexity?
  - AI recommendation generation feasibility?

**4:00 PM - Create estimate doc (60 min)**

- [ ] Estimate Phase 1 tasks (best/likely/worst case)
- [ ] Identify dependencies (backend, AI, infrastructure)
- [ ] Note any blockers or concerns
- [ ] Calculate team capacity (who's available?)

---

### End of Day

**5:00 PM - Slack Update**

Post in #coach-v6-validation:

> **Day 1 Progress:**
>
> ✅ Kickoff completed
> ✅ [Designer] Figma project started, hero component in progress
> ✅ [PM] Recruitment survey live, ads posted
> ✅ [Engineering] Technical review underway
>
> **Tomorrow's Goals:**
>
> - Complete desktop mockups
> - First applicants screened
> - Technical estimates ready
>
> **Blockers:** [List any]

---

## Tuesday, November 14

### Product Designer

**9:00 AM - Continue mockups (3 hours)**

- [ ] Complete health score header (all 3 states)
- [ ] Design proactive coach cards (critical/important/suggestion)
- [ ] Design goals + tasks side-by-side layout
- [ ] Design metrics snapshot section
- [ ] Design chat interface (collapsed state)

**12:00 PM - Lunch break**

**1:00 PM - Add interactions (2 hours)**

- [ ] Add hover states
- [ ] Add active/focused states
- [ ] Add loading skeletons
- [ ] Add transition notes

**3:00 PM - Team review (30 min)**

- [ ] Present designs to PM and Engineering
- [ ] Collect feedback
- [ ] Note changes needed

**3:30 PM - Iterate (2 hours)**

- [ ] Make requested changes
- [ ] Polish visual details
- [ ] Ensure consistency

**5:30 PM - EOD update in Slack**

---

### Product Manager

**9:00 AM - Review applicants (1 hour)**

- [ ] Check Google Form responses
- [ ] Screen against criteria
- [ ] Tag qualified candidates in spreadsheet

**10:00 AM - Contact candidates (2 hours)**

- [ ] Email top 15 candidates (aiming for 10 confirmed)
- [ ] Offer available time slots
- [ ] Send Calendly link (if using)

**12:00 PM - Lunch break**

**1:00 PM - Continue recruitment (1 hour)**

- [ ] Boost posts in groups (if allowed)
- [ ] Respond to questions
- [ ] Follow up with interested parties

**2:00 PM - Finalize user testing script (2 hours)**

- [ ] Review script with team
- [ ] Practice run-through
- [ ] Refine questions
- [ ] Print/prepare note-taking template

**4:00 PM - Schedule confirmations (1 hour)**

- [ ] Confirm 10 participants
- [ ] Send calendar invites
- [ ] Update tracking spreadsheet

**5:00 PM - Prep testing environment (30 min)**

- [ ] Test Zoom settings
- [ ] Test screen recording
- [ ] Prepare note-taking document

---

### Engineering Lead

**9:00 AM - Complete estimates (2 hours)**

- [ ] Finalize effort estimates for Phase 1
- [ ] Create project timeline (Gantt chart or similar)
- [ ] Identify team composition needed

**11:00 AM - Architecture planning (2 hours)**

- [ ] Sketch high-level architecture
- [ ] Plan component hierarchy
- [ ] Plan API endpoints needed
- [ ] Plan database schema changes

**1:00 PM - Lunch break**

**2:00 PM - Risk assessment (2 hours)**

- [ ] List technical risks
- [ ] Propose mitigations
- [ ] Identify POC items (if needed)

**4:00 PM - Create RFC doc (1 hour)**

- [ ] Write Request for Comments document
- [ ] Share with engineering team
- [ ] Request feedback by Friday

---

## Wednesday, November 15

### Product Designer

**9:00 AM - Mobile responsive design (3 hours)**

- [ ] Adapt health score for mobile (80px height)
- [ ] Design coach cards as carousel
- [ ] Design tabbed navigation (Goals/Tasks/Metrics)
- [ ] Design chat as bottom sheet

**12:00 PM - Lunch break**

**1:00 PM - Create prototype (3 hours)**

- [ ] Link screens in Figma
- [ ] Add click interactions
- [ ] Add realistic data (use sample businesses)
- [ ] Test flow

**4:00 PM - Internal testing (1 hour)**

- [ ] Test prototype with PM
- [ ] Fix any broken links
- [ ] Ensure all paths work

**5:00 PM - Share prototype link**

- [ ] Post in Slack
- [ ] Request team feedback
- [ ] Note: feedback due by tomorrow morning

---

### Product Manager

**9:00 AM - Confirm all participants (1 hour)**

- [ ] Send reminder emails (24 hours before)
- [ ] Confirm Zoom links work
- [ ] Update schedule with any changes

**10:00 AM - Finalize testing materials (2 hours)**

- [ ] Prepare comparison: V5 vs V6 screenshots
- [ ] Load test data into prototype
- [ ] Create consent form (if needed)
- [ ] Print note-taking templates

**12:00 PM - Lunch break**

**1:00 PM - Practice session (1 hour)**

- [ ] Full run-through with colleague
- [ ] Time each section
- [ ] Refine script
- [ ] Practice note-taking

**2:00 PM - Data baseline (2 hours)**

- [ ] Pull current metrics from analytics:
  - DAU/MAU ratio
  - Average session time
  - Health score view rate
  - Task completion rate
  - Feature usage stats
- [ ] Document in spreadsheet
- [ ] Share with team

**4:00 PM - Prep for Week 2 (1 hour)**

- [ ] Review all 10 participant profiles
- [ ] Note industry-specific questions for each
- [ ] Prepare backup participants (in case of no-shows)

---

### Engineering Team

**9:00 AM - Team sync (1 hour)**

- [ ] Present estimates and architecture
- [ ] Discuss risks and mitigations
- [ ] Answer team questions
- [ ] Get buy-in

**10:00 AM - Set up dev environment (2 hours)**

- [ ] Create feature branch: `feature/coach-v6`
- [ ] Set up Storybook for components
- [ ] Set up test environment

**12:00 PM - Lunch break**

**1:00 PM - Create component scaffolds (3 hours)**

- [ ] Basic file structure
- [ ] Component shells (no logic yet)
- [ ] Type definitions
- [ ] Placeholder data

*Note: This is optional - only if validation likely to succeed*

---

## Thursday, November 16

### Product Designer

**9:00 AM - Address feedback (2 hours)**

- [ ] Review team feedback from Wednesday
- [ ] Make design changes
- [ ] Update prototype

**11:00 AM - Create comparison materials (2 hours)**

- [ ] Side-by-side screenshots (V5 vs V6)
- [ ] Document key differences
- [ ] Prepare talking points for PM

**1:00 PM - Lunch break**

**2:00 PM - Polish and finalize (3 hours)**

- [ ] Final visual polish
- [ ] Ensure all states are designed
- [ ] Create design annotations
- [ ] Prepare handoff document (for engineers)

**5:00 PM - Lock prototype**

- [ ] Final version ready for testing
- [ ] Share link with PM
- [ ] No more changes until after testing

---

### Product Manager

**9:00 AM - Final prep (2 hours)**

- [ ] Review all participant profiles
- [ ] Prepare industry-specific questions
- [ ] Test Zoom setup again
- [ ] Prepare gift card codes

**11:00 AM - Dry run #2 (1 hour)**

- [ ] Full practice session with designer
- [ ] Use final prototype
- [ ] Time exactly 20 minutes
- [ ] Refine any rough spots

**12:00 PM - Lunch break**

**1:00 PM - Send 24-hour reminders (1 hour)**

- [ ] Email all Friday participants
- [ ] Include Zoom link again
- [ ] Set calendar reminders

**2:00 PM - Conduct first test sessions (3 hours)**

- [ ] Session 1: 2:00 PM
- [ ] Break: 2:30 PM (document notes)
- [ ] Session 2: 3:00 PM
- [ ] Break: 3:30 PM (document notes)

**5:00 PM - Review day 1 sessions**

- [ ] Note initial patterns
- [ ] Identify any script changes needed
- [ ] Send gift cards to participants

---

## Friday, November 17

### Product Manager - Testing Day

**9:30 AM - Prep for sessions**

- [ ] Review notes from Thursday
- [ ] Adjust questions if needed
- [ ] Test Zoom again

**10:00 AM - Morning sessions (3 hours)**

- [ ] Session 3: 10:00 AM
- [ ] Break: 10:30 AM
- [ ] Session 4: 11:00 AM
- [ ] Break: 11:30 AM
- [ ] Session 5: 12:00 PM

**1:00 PM - Lunch & initial analysis**

- [ ] Review morning patterns
- [ ] Update tracking spreadsheet
- [ ] Send gift cards

**2:00 PM - Afternoon sessions (3 hours)**

- [ ] Session 6: 2:00 PM
- [ ] Break: 2:30 PM
- [ ] Session 7: 3:00 PM
- [ ] Break: 3:30 PM

**5:00 PM - Day wrap-up**

- [ ] Send gift cards
- [ ] Document insights
- [ ] Slack update to team

---

### Design & Engineering - Available for Support

**Both teams on standby:**

- [ ] Monitor Slack for urgent questions
- [ ] Be available if PM needs design clarification
- [ ] Start thinking about next week

---

## End of Week 1

**5:30 PM - Team Standup (30 min)**

**Agenda:**

1. Week 1 accomplishments
2. Testing insights so far (7 sessions complete)
3. Plan for Week 2
4. Any adjustments needed?

**Deliverables Check:**

- [ ] Figma prototype complete ✓
- [ ] 10 participants recruited ✓
- [ ] 7 testing sessions complete ✓
- [ ] Technical estimates ready ✓

**Week 2 Preview:**

- Monday-Wednesday: 3 more testing sessions
- Thursday: Analysis and synthesis
- Friday: Go/No-Go decision meeting

---

## Success Metrics (Track Throughout Week)

**Recruitment:**

- Target: 15 applicants screened, 10 confirmed
- Actual: ___

**Design:**

- Target: Prototype complete by Wednesday
- Actual: ___

**Testing (first 7 sessions):**

- Comprehension rate: ___/7 understood health score
- Preference: ___/7 prefer fitness dashboard
- Willing to pay $150+: ___/7

**Early signals:**

- [ ] Are we on track for 70%+ preference?
- [ ] Any major usability issues discovered?
- [ ] Do we need to iterate the prototype?

---

## Communication Plan

**Daily Slack Updates (5 PM):**

- What got done today
- What's planned for tomorrow
- Any blockers

**Leadership Updates:**

- Monday: Sprint kicked off
- Wednesday: Prototype complete, testing starting
- Friday: 7/10 sessions complete, early signals

**All-Hands Mention:**

- Brief update at company meeting
- "We're validating a major redesign, stay tuned"

---

## Budget Tracking

| Item | Budgeted | Actual | Notes |
|------|----------|--------|-------|
| Design hours (40 @ $150) | $6,000 | TBD | |
| Participant incentives (10 × $100) | $1,000 | TBD | |
| Survey platform | $50 | TBD | Google Forms free |
| **Total** | **$7,050** | **TBD** | Under budget target |

---

## Risk Log

| Risk | Likelihood | Impact | Mitigation | Status |
|------|------------|--------|------------|--------|
| Can't recruit 10 participants | Low | High | Post in multiple channels, offer $150 if needed | ⚠️ Monitor |
| Prototype takes longer than expected | Medium | Medium | Designer working full-time, buffer built in | ✅ On track |
| Technical feasibility concerns | Low | High | Engineering reviewing in parallel | ✅ Clear so far |
| Testing sessions reveal major issues | Medium | High | Have Week 2 buffer for iteration | 🔄 TBD |

---

## Next Steps After Week 1

**If testing is going well:**

- Continue Week 2 as planned
- Prepare for go/no-go decision
- Brief leadership on early results

**If testing reveals issues:**

- Schedule emergency design session (Saturday/Sunday)
- Iterate prototype
- Consider extending validation by 1 week

**If can't recruit enough participants:**

- Increase incentive to $150
- Extend recruitment to Monday Week 2
- Consider remote vs local strategies

---

**Document Owner:** Product Manager  
**Version:** 1.0  
**Last Updated:** November 13, 2025
