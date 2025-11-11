# Signup Flow with Plan Selection

## Overview

Updated the signup flow to include plan selection, allowing customers to choose their plan before signing up.

## User Journey

### 1. Landing Page → Signup

Users can start the signup process from multiple entry points:

- **Hero CTA**: "Start free assessment" → `/signup?plan=pilot`
- **Pricing Cards**: Each plan has a CTA that passes the plan ID
  - Pilot: "Try the pilot" → `/signup?plan=pilot`
  - Run: "Start Run plan" → `/signup?plan=run`
  - Scale: "Talk to sales" → `/signup?plan=scale`
- **Header CTA**: "Start your journey" → `/signup` (defaults to pilot)

### 2. Signup Page Structure

The signup page now has **two steps**:

#### Step 1: Plan Selection

- Shows all 3 plans (Pilot, Run, Scale) as radio buttons
- Each plan card displays:
  - Plan name with "Most Popular" badge for Run plan
  - Description
  - Price and billing cadence
  - Visual highlight when selected
- Users can change their plan selection before submitting
- Selected plan is pre-filled from URL parameter (`?plan=pilot`)

#### Step 2: User Information

- **Left sidebar** shows:
  - Dynamic title based on selected plan
  - Selected plan summary with features
  - "Change" button to scroll back to plan selection
  - Badge showing plan benefits
  
- **Right form** collects:
  - Name
  - Business name
  - Email
  - Primary goal (only for Pilot/Run plans, not Scale)
  - Additional information/challenges

### 3. Plan-Specific Behavior

#### Pilot Plan (Free)

- Title: "Welcome! Let's Get to Know Your Business"
- Subtitle: "In 60 seconds, you'll have your business health score and personalized action plan"
- CTA: "Start with Pilot plan"
- Shows goal selection (revenue, cash flow, customers, insights)
- Badge: "Free assessment • No credit card"

#### Run Plan ($79/month)

- Same as Pilot plan
- Badge: "Start immediately after verification"
- CTA: "Start with Run plan"

#### Scale Plan (Custom)

- Title: "Talk to Our Team"
- Subtitle: "Share your details and we'll schedule a personalized demo with our team"
- CTA: "Request demo"
- Hides goal selection
- Shows demo-focused messaging
- Different placeholder: "What challenges are you facing?"

### 4. Form Submission

When user submits:

- Plan ID is included in the API payload: `{ plan: 'pilot' | 'run' | 'scale' }`
- Plan is passed to verification page: `/verify?token=xxx&plan=pilot`
- Existing tool and next parameters are preserved

## Technical Changes

### Files Modified

1. **`apps/smb/src/pages/Signup.tsx`**
   - Added plan selection with Radio.Group
   - Added plan state management from URL params
   - Updated form to conditionally show fields based on plan
   - Updated sidebar to show selected plan summary
   - Added plan-specific messaging and CTAs

2. **`apps/smb/src/pages/LandingPage.tsx`**
   - Added `id` field to pricing plans
   - Updated all pricing CTAs to link to `/signup?plan={id}`
   - Updated hero CTA to `/signup?plan=pilot`
   - Changed secondary hero CTA from "/contact" to "#pricing" anchor

## Design Highlights

### Visual Hierarchy

- **Step 1** (Plan Selection):
  - Eyebrow: "STEP 1 · CHOOSE YOUR PLAN"
  - Radio cards with hover states
  - Selected plan has `ring-2 ring-brand-500` and light background
  - "Most Popular" badge on Run plan

- **Step 2** (User Info):
  - Eyebrow: "STEP 2 · YOUR INFORMATION"
  - Consistent form styling
  - Plan-specific messaging

### Left Sidebar

- Glassmorphism panel with gradient
- Selected plan summary card with:
  - Plan name and price
  - Feature list with checkmarks
  - "Change" button (scrolls to plan selection)
- Dynamic badge based on plan

### Responsive Design

- Mobile: Single column, plan cards stack
- Desktop: Two-column layout with sidebar

## Benefits

1. **Clear Value Proposition**: Users see all plans before committing
2. **Informed Decision**: Plan features and pricing are visible during signup
3. **Flexibility**: Users can change plans before submitting
4. **Conversion Optimization**:
   - Free pilot reduces friction
   - Run plan highlighted as "Most Popular"
   - Scale plan triggers sales conversation
5. **Better Onboarding**: Backend knows user's plan intent immediately

## Next Steps

1. ✅ Plan selection UI implemented
2. ✅ Plan passed to API and verification flow
3. ⏳ Backend: Handle plan assignment during signup
4. ⏳ Welcome flow: Customize onboarding based on selected plan
5. ⏳ Analytics: Track plan selection conversion rates
