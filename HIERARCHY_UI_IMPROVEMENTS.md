# Tenant → Project → Plan Hierarchy - UI Improvements

## 📊 Overview

The application has a three-level organizational hierarchy, but it wasn't visually clear to users. These improvements make the structure obvious and help users understand how their business plans are organized.

## 🏗️ Hierarchy Structure

```
📊 Workspace (Tenant)
    └─ Your company's main account
    └─ Stores tenant_id, subscription plan, usage limits
    
    📁 Projects
        └─ Organize plans by department, initiative, or business unit
        └─ Examples: "Q1 2024", "Restaurant A", "Cost Optimization"
        └─ Each project has a unique project_id
        
        📋 Plans
            └─ Specific business plans with goals, stages, and actions
            └─ Examples: "Reduce food waste 20%", "Increase revenue 15%"
            └─ Each plan has versions, quick wins, estimated duration
```

## ✨ What Changed

### 1. **TopNav Component** (`apps/ui/src/components/TopNav.tsx`)

**Before:**

- Project selector was a plain dropdown with minimal styling
- No label indicating what the dropdown was for
- "+ New" button was ambiguous

**After:**

- Added "Project:" label to clearly identify the dropdown
- Enhanced styling with background color and border
- Changed button text from "+ New" to "+ New Project" for clarity
- Visual hierarchy with gray background container

**Code Changes:**

```tsx
// Added visual container and label
<div className="hidden md:flex items-center gap-2 bg-gray-50 px-3 py-1.5 rounded-lg border border-gray-200">
  <span className="text-xs font-medium text-gray-500 uppercase tracking-wide">Project:</span>
  <select>...</select>
  <button>+ New Project</button>
</div>
```

### 2. **PlanVersionsSidebar Component** (`apps/ui/src/components/PlanVersionsSidebar.tsx`)

**Before:**

- Header showed "My Plans (5)" with small text "in ProjectName"
- No visual indication of hierarchy

**After:**

- Added breadcrumb-style hierarchy display in header
- Shows: `📊 Workspace → 📁 Project Name → 5 Plans`
- Enhanced header with gradient background
- Button text updated to "Create New Plan in [Project Name]"

**Code Changes:**

```tsx
// Added hierarchy breadcrumb
<div className="flex items-center gap-2 text-xs text-gray-600 bg-white/60 px-3 py-2 rounded-md">
  <span>📊 Workspace</span>
  <span>→</span>
  <span>📁 {projectName}</span>
  <span>→</span>
  <span>{plans.length} Plans</span>
</div>
```

### 3. **PlanSelector Component** (`apps/ui/src/components/PlanSelector.tsx`)

**Before:**

- No indication of organizational context
- Generic welcome message

**After:**

- Added visual hierarchy breadcrumb at the top
- Added informational card explaining the three-level structure (shown when no plans exist)
- Updated messaging to include current project name
- Educational content for first-time users

**Code Changes:**

```tsx
// Added props to receive context
type PlanSelectorProps = {
  // ... existing props
  currentProjectName?: string;
  tenantName?: string;
};

// Added hierarchy display
<div className="inline-flex items-center gap-2 ...">
  <span>📊 {tenantName}</span>
  <span>→</span>
  <span>📁 {currentProjectName}</span>
  <span>→</span>
  <span>📋 Plans</span>
</div>

// Added educational info card
<div className="rounded-xl bg-gradient-to-r from-blue-100 ...">
  <h3>How It Works: Organize Your Business Plans</h3>
  {/* Explains Workspace → Projects → Plans hierarchy */}
</div>
```

### 4. **HomePage Component** (`apps/ui/src/pages/HomePage.tsx`)

**Before:**

- PlanSelector received minimal props

**After:**

- Passes current project name and tenant name to PlanSelector
- Enables contextual hierarchy display

**Code Changes:**

```tsx
<PlanSelector
  plans={savedPlans}
  onSelectPlan={handleSelectPlan}
  onCreateNew={handleCreateNewPlan}
  onDeletePlan={handleDeletePlan}
  currentProjectName={projects.find(p => p.project_id === currentProjectId)?.name}
  tenantName={profile?.name}
/>
```

## 🎯 Benefits

### For Users

1. **Clear Context**: Always know which workspace and project you're working in
2. **Easy Navigation**: Visual breadcrumbs show hierarchy at a glance
3. **Reduced Confusion**: Icons and labels make structure obvious
4. **Better Onboarding**: Educational card explains the organizational model

### For Developers

1. **Consistent Pattern**: Hierarchy display is uniform across components
2. **Props-Based**: Easy to pass context down component tree
3. **Type Safe**: TypeScript interfaces ensure correct data flow
4. **Maintainable**: Clear separation of concerns

## 📁 Files Modified

1. **`apps/ui/src/components/TopNav.tsx`**
   - Enhanced project selector with label and styling
   - Changed button text for clarity

2. **`apps/ui/src/components/PlanVersionsSidebar.tsx`**
   - Added hierarchy breadcrumb in header
   - Updated button text with project context

3. **`apps/ui/src/components/PlanSelector.tsx`**
   - Added hierarchy display at top
   - Added educational info card
   - Updated messaging with context
   - Added new props for tenant/project names

4. **`apps/ui/src/pages/HomePage.tsx`**
   - Passes hierarchy context to PlanSelector

## 🔄 Data Flow

```typescript
// User Authentication
AuthContext → user.tenant_id

// Profile & Projects
useAccount() → {
  profile: TenantProfile (includes tenant_id, name, plan)
  projects: ProjectSummary[] (includes project_id, name)
}

// Current Context
HomePage → {
  currentProjectId: string
  currentPlanId: string
}

// Plan Storage (localStorage)
planPersistence → {
  scopedKey: "dyocense-plans-{tenantId}-{projectId}"
  getSavedPlans(tenantId, projectId)
  savePlan(tenantId, plan, projectId)
}
```

## 🚀 Usage Examples

### Switching Projects

1. User opens project dropdown in TopNav (labeled "Project:")
2. Selects different project
3. HomePage clears active plan and reloads plans for new project
4. All components update to show new project context

### Creating New Plan

1. User clicks "+ New Plan" button
2. Sidebar shows "Create New Plan in [Project Name]"
3. Plan is scoped to current tenant and project
4. Saved with localStorage key: `dyocense-plans-{tenantId}-{projectId}`

### Viewing Plans List

1. User clicks menu icon in TopNav
2. PlanVersionsSidebar opens
3. Header shows: `📊 Workspace → 📁 ProjectName → X Plans`
4. All plans are filtered to current project

## 🎨 Visual Design

### Color Scheme

- **Tenant/Workspace**: Gray tones (neutral, high-level)
- **Project**: Primary blue (active selection)
- **Plans**: Gray/black (content level)

### Icons

- **📊 Workspace**: Business/organizational level
- **📁 Project**: Container/folder metaphor
- **📋 Plans**: Document/actionable items

### Layout

- **Breadcrumbs**: Horizontal flow with arrows (→)
- **Cards**: Rounded, shadowed, with gradients
- **Containers**: Subtle backgrounds to group related items

## 📝 Notes

### localStorage Scoping

Plans are scoped by both tenant and project:

```typescript
// Key format
"dyocense-plans-{tenantId}-{projectId}"

// Example
"dyocense-plans-rest123-project-abc"
```

### Active Selection Persistence

```typescript
// Project selection
localStorage: "dyocense-active-project-{tenantId}"

// Plan selection  
localStorage: "dyocense-plans-active-{tenantId}-{projectId}"
```

### Future Enhancements

1. **Breadcrumb Navigation**: Make hierarchy breadcrumbs clickable
2. **Project Switcher Modal**: Grid view of all projects with plan counts
3. **Workspace Settings**: Add page to manage tenant-level settings
4. **Plan Tags**: Add project-specific tags for better organization
5. **Search Across Projects**: Global search that spans all projects
6. **Recent Activity**: Show cross-project activity feed

## ✅ Testing Checklist

- [x] Project selector shows correct label
- [x] Hierarchy breadcrumbs appear in PlanSelector
- [x] Hierarchy breadcrumbs appear in PlanVersionsSidebar
- [x] Educational card shows for empty plan list
- [x] Button text includes project context
- [x] TypeScript compilation succeeds
- [x] No console errors

## 🔗 Related Files

- **API Types**: `apps/ui/src/lib/api.ts` (TenantProfile, ProjectSummary)
- **Hooks**: `apps/ui/src/hooks/useAccount.ts` (loads tenant & projects)
- **Storage**: `apps/ui/src/lib/planPersistence.ts` (scoped localStorage)
- **Auth**: `apps/ui/src/context/AuthContext.tsx` (user session)

---

**Result**: The organizational hierarchy is now clear and consistent throughout the UI, making it easier for users to understand how their business plans are structured and organized.
