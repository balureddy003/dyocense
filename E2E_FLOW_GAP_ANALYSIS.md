# End-to-End Flow Gap Analysis: Tenant/Project/Plan Hierarchy

**Date:** November 7, 2025  
**Scope:** Complete user journey analysis for workspace/project/plan context propagation  
**Priority:** HIGH - Affects user experience and data organization

---

## Executive Summary

After implementing the Priority 1 fix for hardcoded workspace/project labels, I've identified **7 critical gaps** in the end-to-end flow where tenant and project context is missing, inconsistent, or not properly propagated through the component hierarchy.

### Impact Level: MEDIUM-HIGH 🟡

While the immediate visual breadcrumb issue is fixed, several components and flows still lack proper context awareness, leading to:

- Inconsistent user experience across different views
- Potential data isolation issues
- Missing context in AI assistant interactions
- Incomplete hierarchy display in various UI components

---

## Current State: Data Flow Map

```
┌─────────────────────────────────────────────────────────────┐
│ Authentication Layer                                         │
│ ├─ user (AuthContext)                                       │
│ └─ token                                                     │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│ Account Layer (useAccount hook)                             │
│ ├─ profile: TenantProfile                                   │
│ │  ├─ tenant_id: string                                     │
│ │  ├─ name: string ✅ (NOW PASSED TO BREADCRUMBS)          │
│ │  ├─ owner_email                                           │
│ │  ├─ plan: SubscriptionPlan                               │
│ │  └─ usage stats                                           │
│ └─ projects: ProjectSummary[]                               │
│    ├─ project_id: string                                    │
│    ├─ name: string ✅ (NOW PASSED TO BREADCRUMBS)           │
│    ├─ description                                            │
│    └─ timestamps                                             │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│ HomePage (State Management)                                  │
│ ├─ currentProjectId: string | null                          │
│ ├─ savedPlans: SavedPlan[]                                  │
│ ├─ currentPlanId: string | null                             │
│ └─ generatedPlan: PlanOverview | null                       │
└─────────────────────────────────────────────────────────────┘
                           ↓
        ┌──────────────────┴──────────────────┐
        ↓                                      ↓
┌─────────────────┐                  ┌─────────────────┐
│ PlanSelector    │                  │ AgentAssistant  │
│ ✅ tenantName   │                  │ ❌ tenantName   │
│ ✅ projectName  │                  │ ❌ projectName  │
└─────────────────┘                  └─────────────────┘
        ↓                                      ↓
┌─────────────────┐                  ┌─────────────────┐
│ Versions        │                  │ TopNav          │
│ Sidebar         │                  │ ⚠️  partial     │
│ ✅ tenantName   │                  │    context      │
│ ✅ projectName  │                  └─────────────────┘
└─────────────────┘
```

---

## Gap Analysis: 7 Critical Issues

### Gap #1: AgentAssistant Missing Context 🔴 CRITICAL

**Location:** `apps/ui/src/components/AgentAssistant.tsx`

**Current Props:**

```typescript
export type AgentAssistantProps = {
  onPlanGenerated?: (plan: PlanOverview) => void;
  profile?: TenantProfile | null;
  seedGoal?: string;
  startNewPlanSignal?: number;
};
```

**Problem:**

- Has `profile` (contains tenant info) ✅
- **Missing `projectName`** ❌
- **Missing `currentProjectId`** ❌
- Cannot display project context to user
- Cannot pass project context to AI prompts
- AI doesn't know which project the plan is for

**Impact:**

- AI assistant doesn't know project context when generating plans
- User doesn't see which project they're planning for in the assistant
- Generated plans lack project-specific context
- Multi-project users get confused

**Recommended Fix:**

```typescript
export type AgentAssistantProps = {
  onPlanGenerated?: (plan: PlanOverview) => void;
  profile?: TenantProfile | null;
  projectId?: string | null;          // ADD THIS
  projectName?: string;                // ADD THIS
  seedGoal?: string;
  startNewPlanSignal?: number;
};
```

**Usage in HomePage:**

```typescript
<AgentAssistant
  onPlanGenerated={handlePlanGenerated}
  profile={profile}
  projectId={currentProjectId}  // ADD
  projectName={projects.find(p => p.project_id === currentProjectId)?.name}  // ADD
  seedGoal={seedGoal}
  startNewPlanSignal={newPlanSignal}
/>
```

**Estimated Effort:** 1-2 hours

---

### Gap #2: TopNav Incomplete Context Display 🟡 MEDIUM

**Location:** `apps/ui/src/components/TopNav.tsx`

**Current Props:**

```typescript
interface TopNavProps {
  planName?: string;
  planVersion?: number;
  projectOptions?: Array<{ id: string; name: string }>;
  currentProjectId?: string | null;
  // ... other props
}
```

**Problem:**

- Has project picker ✅
- **Missing tenant name display** ❌
- No breadcrumb showing full hierarchy
- User can't see which workspace they're in
- Inconsistent with PlanVersionsSidebar breadcrumb

**Impact:**

- Users lose context when in "agent" or "results" mode
- No visual confirmation of current workspace
- Breaks hierarchy consistency

**Recommended Fix:**

Add tenant name and optional breadcrumb display:

```typescript
interface TopNavProps {
  // ... existing props
  tenantName?: string;              // ADD THIS
  showHierarchyBreadcrumb?: boolean; // ADD THIS (optional feature flag)
}
```

Add breadcrumb display in TopNav (optional enhancement):

```typescript
{showHierarchyBreadcrumb && tenantName && (
  <div className="text-xs text-gray-600 flex items-center gap-2">
    <span>📊 {tenantName}</span>
    {currentProjectId && projectOptions && (
      <>
        <span>→</span>
        <span>📁 {projectOptions.find(p => p.id === currentProjectId)?.name}</span>
      </>
    )}
  </div>
)}
```

**Estimated Effort:** 2-3 hours

---

### Gap #3: PlanNameModal Missing Context 🟡 MEDIUM

**Location:** `apps/ui/src/components/PlanNameModal.tsx`

**Current Props:**

```typescript
type PlanNameModalProps = {
  open: boolean;
  onClose: () => void;
  onSave: (name: string) => void;
  onSkip: () => void;
  currentName?: string;
  aiGeneratedTitle?: string;
};
```

**Problem:**

- No context about which project the plan belongs to
- User doesn't see "Saving plan in [Project Name]" confirmation
- Missing workspace/project breadcrumb in modal

**Impact:**

- Users unsure which project they're saving to
- Risk of saving to wrong project if they recently switched
- No visual confirmation of context

**Recommended Fix:**

```typescript
type PlanNameModalProps = {
  // ... existing props
  tenantName?: string;     // ADD THIS
  projectName?: string;    // ADD THIS
};
```

Add context display in modal:

```typescript
{(tenantName || projectName) && (
  <div className="mb-4 p-3 bg-blue-50 rounded-lg border border-blue-200">
    <div className="text-xs text-gray-600 flex items-center gap-2">
      {tenantName && <span>📊 {tenantName}</span>}
      {tenantName && projectName && <span>→</span>}
      {projectName && <span>📁 {projectName}</span>}
    </div>
    <p className="text-sm text-gray-700 mt-1">
      Saving plan in {projectName || "current project"}
    </p>
  </div>
)}
```

**Estimated Effort:** 1 hour

---

### Gap #4: VersionComparisonModal Missing Context 🟡 MEDIUM

**Location:** `apps/ui/src/components/VersionComparisonModal.tsx`

**Problem:**

- Shows version comparison without project/tenant context
- Users can't tell which project the versions belong to
- Important for multi-project scenarios

**Recommended Fix:**

Add context props and display breadcrumb similar to PlanNameModal.

**Estimated Effort:** 1 hour

---

### Gap #5: MetricsPanel Lacks Project Context 🟢 LOW

**Location:** `apps/ui/src/components/MetricsPanel.tsx`

**Current Props:**

```typescript
export type MetricsPanelProps = {
  plan?: PlanOverview | null;
  onExportClick?: () => void;
  onShareClick?: () => void;
};
```

**Problem:**

- Displays plan metrics without project/tenant context
- Metrics may be confusing in multi-project setups
- No way to show "Metrics for [Project Name]"

**Impact:**

- Low - metrics are typically viewed in context
- Could be confusing for power users

**Recommended Fix:**

```typescript
export type MetricsPanelProps = {
  plan?: PlanOverview | null;
  projectName?: string;    // ADD THIS
  onExportClick?: () => void;
  onShareClick?: () => void;
};
```

**Estimated Effort:** 30 minutes

---

### Gap #6: ExecutionPanel Missing Project Context 🟢 LOW

**Location:** `apps/ui/src/components/ExecutionPanel.tsx`

**Similar Issue:** Shows execution details without project context

**Estimated Effort:** 30 minutes

---

### Gap #7: localStorage Keys Missing Hierarchy 🟡 MEDIUM-HIGH

**Location:** Multiple files using localStorage

**Current Implementation:**

```typescript
// planPersistence.ts
function scopedKey(tenantId: string, projectId?: string | null): string {
  return `${STORAGE_KEY_PREFIX}-${tenantId}${projectId ? `-${projectId}` : ""}`;
}

// HomePage.tsx
const storageKey = `dyocense-active-project-${profile.tenant_id}`;
const key = `dyocense-draft-planname-${profile?.tenant_id || 'anon'}-${currentPlanId || 'new'}`;
```

**Problem:**

- ✅ Plans are scoped to tenant + project
- ✅ Active project is scoped to tenant
- ⚠️  Draft plan names are scoped but use 'anon' fallback
- ❌ Some localStorage keys don't include proper scoping
- ❌ No consistent naming convention

**Impact:**

- Potential data leakage between tenants/projects
- Confusion when switching contexts
- Hard to debug localStorage issues

**Recommended Fix:**

Create centralized localStorage key generator:

```typescript
// lib/storageKeys.ts
export const STORAGE_PREFIX = 'dyocense';

export const storageKeys = {
  // Plans
  plans: (tenantId: string, projectId?: string | null) =>
    `${STORAGE_PREFIX}-plans-${tenantId}${projectId ? `-${projectId}` : ''}`,
  
  activePlan: (tenantId: string, projectId?: string | null) =>
    `${STORAGE_PREFIX}-active-plan-${tenantId}${projectId ? `-${projectId}` : ''}`,
  
  // Projects
  activeProject: (tenantId: string) =>
    `${STORAGE_PREFIX}-active-project-${tenantId}`,
  
  // Plan drafts
  planDraft: (tenantId: string, planId: string) =>
    `${STORAGE_PREFIX}-draft-plan-${tenantId}-${planId}`,
  
  // Preferences
  skipPlanNaming: (tenantId: string, planId?: string) =>
    planId
      ? `${STORAGE_PREFIX}-skip-name-${tenantId}-${planId}`
      : `${STORAGE_PREFIX}-skip-name-pending-${tenantId}`,
  
  // User preferences
  userPreferences: (userId: string) =>
    `${STORAGE_PREFIX}-preferences-${userId}`,
};
```

**Benefits:**

- Consistent naming across app
- Type-safe key generation
- Easy to audit storage usage
- Prevents typos and bugs

**Estimated Effort:** 2-3 hours (requires careful refactoring)

---

## Additional Observations

### ✅ What's Working Well

1. **planPersistence.ts** - Already properly scopes plans to tenant + project
2. **PlanSelector** - Correctly displays tenant and project names
3. **PlanVersionsSidebar** - Now correctly displays context after Priority 1 fix
4. **Project switching logic** - Works correctly with localStorage persistence
5. **useAccount hook** - Properly loads tenant profile and projects

### ⚠️  Areas of Concern

1. **Project Name Resolution Performance**

   ```typescript
   // This pattern appears multiple times:
   projects.find(p => p.project_id === currentProjectId)?.name
   ```

   - Runs on every render
   - Could be optimized with useMemo
   - Should be centralized

2. **Fallback Handling Inconsistency**
   - Some places: `projectName || "Project"`
   - Some places: `currentProjectName || ''`
   - Some places: No fallback
   - Should standardize

3. **Type Safety Issues**
   - `profile?.name` might be undefined
   - `projects.find()?.name` might be undefined
   - Need proper null handling everywhere

---

## Recommended Implementation Priority

### Phase 1: Critical Fixes (4-6 hours)

1. ✅ **COMPLETED:** Fix PlanVersionsSidebar breadcrumb
2. **Gap #1:** Add project context to AgentAssistant (1-2 hours)
3. **Gap #3:** Add context to PlanNameModal (1 hour)
4. **Gap #2:** Enhance TopNav with tenant context (2-3 hours)

### Phase 2: Medium Priority (3-4 hours)

5. **Gap #4:** Add context to VersionComparisonModal (1 hour)
6. **Create shared HierarchyBreadcrumb component** (2 hours)
7. **Standardize project name resolution** (1 hour)

### Phase 3: Enhancements (3-5 hours)

8. **Gap #7:** Refactor localStorage keys (2-3 hours)
9. **Gap #5:** Add context to MetricsPanel (30 min)
10. **Gap #6:** Add context to ExecutionPanel (30 min)
11. **Performance optimization** (1-2 hours)

**Total Estimated Effort:** 10-15 hours

---

## Testing Checklist

After implementing fixes, verify:

### Context Display

- [ ] Tenant name shows in all breadcrumbs
- [ ] Project name shows in all breadcrumbs
- [ ] Context persists across page refreshes
- [ ] Context updates when switching projects

### Multi-Tenant Scenarios

- [ ] Switching tenants clears previous tenant's data
- [ ] Plans are isolated by tenant + project
- [ ] No data leakage between tenants

### Multi-Project Scenarios

- [ ] Switching projects shows correct context
- [ ] Plans load for correct project
- [ ] Active project persists

### AI Assistant

- [ ] Shows current project in assistant header
- [ ] Generates plans with project awareness
- [ ] Handles project switching gracefully

### Edge Cases

- [ ] New user with no projects
- [ ] User with one project (no switching needed)
- [ ] Very long tenant/project names
- [ ] Rapid project switching
- [ ] Offline/online transitions

---

## Code Quality Improvements

### 1. Create Centralized Context Hook

```typescript
// hooks/useHierarchyContext.ts
import { useMemo } from 'react';
import { useAccount } from './useAccount';

export function useHierarchyContext(currentProjectId: string | null) {
  const { profile, projects } = useAccount();
  
  return useMemo(() => {
    const tenantName = profile?.name;
    const currentProject = projects.find(p => p.project_id === currentProjectId);
    const projectName = currentProject?.name;
    
    return {
      tenantId: profile?.tenant_id,
      tenantName: tenantName || 'Workspace',
      projectId: currentProjectId,
      projectName: projectName || 'Project',
      hasContext: !!(tenantName && projectName),
    };
  }, [profile, projects, currentProjectId]);
}
```

**Usage:**

```typescript
const { tenantName, projectName, hasContext } = useHierarchyContext(currentProjectId);
```

### 2. Create Shared Breadcrumb Component

```typescript
// components/HierarchyBreadcrumb.tsx
type HierarchyBreadcrumbProps = {
  tenantName?: string;
  projectName?: string;
  planName?: string;
  className?: string;
  size?: 'sm' | 'md' | 'lg';
};

export function HierarchyBreadcrumb({
  tenantName,
  projectName,
  planName,
  className = '',
  size = 'sm',
}: HierarchyBreadcrumbProps) {
  const textSize = size === 'lg' ? 'text-base' : size === 'md' ? 'text-sm' : 'text-xs';
  
  return (
    <div className={`inline-flex items-center gap-2 ${textSize} text-gray-600 ${className}`}>
      {tenantName && (
        <>
          <span className="font-semibold text-gray-700">📊 {tenantName}</span>
          {(projectName || planName) && <span className="text-gray-400">→</span>}
        </>
      )}
      {projectName && (
        <>
          <span className="font-semibold text-primary">📁 {projectName}</span>
          {planName && <span className="text-gray-400">→</span>}
        </>
      )}
      {planName && (
        <span className="font-semibold text-gray-700">📋 {planName}</span>
      )}
    </div>
  );
}
```

### 3. Standardize Prop Naming

Create consistent prop pattern across all components:

```typescript
// Standard context props (add to all relevant components)
type HierarchyContextProps = {
  tenantName?: string;
  projectId?: string | null;
  projectName?: string;
};

// Usage in component props:
type MyComponentProps = HierarchyContextProps & {
  // component-specific props
};
```

---

## Risk Assessment

### Low Risk Changes ✅

- Adding optional props to components
- Displaying context in UI
- Creating new utility functions

### Medium Risk Changes ⚠️

- Refactoring localStorage keys (needs careful testing)
- Changing prop names (needs comprehensive search/replace)
- Performance optimizations (needs benchmarking)

### High Risk Changes 🔴

- Modifying core data persistence logic
- Changing authentication/authorization flow
- Database schema changes

**Current Recommendation:** All proposed changes are Low-Medium risk.

---

## Success Metrics

After implementation, we should see:

1. **User Confusion Reduced:**
   - Support tickets about "which workspace am I in?" → 0
   - User surveys show improved context awareness

2. **Visual Consistency:**
   - All breadcrumbs show same format
   - Context visible in all relevant screens

3. **Technical Debt Reduced:**
   - Centralized context management
   - Consistent naming conventions
   - Type-safe implementations

4. **Performance:**
   - No regression in load times
   - Optimized context lookups

---

## Conclusion

The Priority 1 fix successfully addresses the most visible gap (hardcoded breadcrumb labels), but there are **7 additional gaps** that should be addressed for a complete, consistent user experience.

### Immediate Action Items

1. **Gap #1 (AgentAssistant)** - Most critical for user experience
2. **Gap #3 (PlanNameModal)** - Prevents save confusion
3. **Gap #2 (TopNav)** - Completes visual consistency

These 3 fixes would address ~80% of the user-facing issues and take approximately 4-6 hours total.

### Long-term Improvements

- Create shared utilities (HierarchyBreadcrumb, useHierarchyContext)
- Refactor localStorage key management
- Add context to all relevant components
- Performance optimizations

**Next Steps:** Prioritize Gap #1 (AgentAssistant) as it directly impacts the core user workflow of plan generation.
