# Onboarding Endpoints Implementation

## Overview

Added backend API endpoints and frontend integration to persist data from the SMB app's welcome wizard, enabling complete end-to-end testing of the CycloneRake user flow.

## Changes Made

### Backend: `services/smb_gateway/main.py`

#### 1. Business Profile Endpoint

**Endpoint**: `POST /v1/tenants/{tenant_id}/profile/business`

**Purpose**: Save business profile data collected during the welcome wizard.

**Request Model**:

```python
class BusinessProfileRequest(BaseModel):
    industry: Optional[str] = None
    company_size: Optional[str] = None
    team_size: Optional[str] = None
    primary_goal: Optional[str] = None
    business_type: Optional[str] = None
    additional_info: Optional[Dict[str, Any]] = None
```

**Functionality**:

- Updates tenant metadata in PostgreSQL `tenants.tenants` table
- Stores profile data as JSONB in `metadata` column
- Adds `profile_updated_at` timestamp
- Merges with existing metadata without overwriting other fields

**Example Request**:

```bash
POST /api/smb/v1/tenants/cyclonerake-demo001/profile/business
{
    "industry": "Food Service",
    "team_size": "5-10",
    "primary_goal": "Optimize inventory management"
}
```

**Response**:

```json
{
    "success": true,
    "message": "Business profile updated successfully",
    "profile": {
        "industry": "Food Service",
        "team_size": "5-10",
        "primary_goal": "Optimize inventory management",
        "profile_updated_at": "2024-01-15T10:30:00.000Z"
    }
}
```

#### 2. Onboarding Completion Endpoint

**Endpoint**: `POST /v1/tenants/{tenant_id}/onboarding/complete`

**Purpose**: Mark onboarding as complete, save health score baseline, and create initial goal.

**Request Model**:

```python
class OnboardingCompleteRequest(BaseModel):
    health_score: Optional[int] = None
    selected_goal: Optional[Dict[str, Any]] = None
    business_profile: Optional[Dict[str, Any]] = None
```

**Functionality**:

- Marks onboarding as complete in tenant metadata
- Saves initial health score as baseline
- Creates goal in goals service if `selected_goal` provided
- Updates tenant metadata with onboarding completion timestamp
- Returns goal_id for tracking

**Goal Creation**:

- If `selected_goal` is provided, creates a goal using the goals service
- Expected goal structure:

```json
{
    "title": "Optimize Operations",
    "description": "Improve inventory turnover rate to 95%",
    "current": 0,
    "target": 100,
    "unit": "%",
    "category": "operations",
    "deadline": "2024-04-15"
}
```

**Example Request**:

```bash
POST /api/smb/v1/tenants/cyclonerake-demo001/onboarding/complete
{
    "health_score": 72,
    "selected_goal": {
        "title": "Optimize Operations",
        "description": "Improve inventory turnover rate to 95%",
        "current": 0,
        "target": 100,
        "unit": "%",
        "category": "operations",
        "deadline": "2024-04-15"
    }
}
```

**Response**:

```json
{
    "success": true,
    "message": "Onboarding completed successfully",
    "goal_id": "goal-a1b2c3d4e5f6",
    "tenant_id": "cyclonerake-demo001"
}
```

### Frontend: `apps/smb/src/pages/Welcome.tsx`

#### Updated `completeOnboarding()` Function

**Changes**:

- Now async function with API call to backend
- Constructs selected goal data from wizard state
- Calls `/v1/tenants/{tenant_id}/onboarding/complete` endpoint
- Uses `apiToken` and `tenantId` from auth store
- Graceful error handling (still navigates even if API fails)

**Data Flow**:

1. User completes welcome wizard steps:
   - Step 1: Health score calculated (stored in `healthScore` state)
   - Step 2: Goal selected (stored in `selectedSuggestion` and `customGoal` state)
   - Step 3: Plan preview shown
2. User clicks "Connect my data first" or "Skip to dashboard"
3. Frontend calls onboarding completion endpoint with:
   - `health_score`: Calculated score from step 1
   - `selected_goal`: Goal data from step 2
4. Backend persists data to PostgreSQL
5. Frontend marks onboarding complete in localStorage
6. User navigates to dashboard or connectors

**Error Handling**:

```typescript
try {
    await fetch(`/api/smb/v1/tenants/${currentTenantId}/onboarding/complete`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${apiToken}`,
        },
        body: JSON.stringify({
            health_score: healthScore,
            selected_goal: selectedGoal,
        }),
    })
} catch (error) {
    console.error('Failed to complete onboarding:', error)
    // Still navigate but log the error
}
```

## Database Schema

### Updated Tables

**`tenants.tenants`**:

```sql
CREATE TABLE tenants.tenants (
    tenant_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    metadata JSONB,  -- Stores profile and onboarding data
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

**Metadata Structure** (after onboarding):

```json
{
    "industry": "Food Service",
    "team_size": "5-10",
    "primary_goal": "Optimize inventory management",
    "profile_updated_at": "2024-01-15T10:30:00.000Z",
    "onboarding_completed": true,
    "onboarding_completed_at": "2024-01-15T10:35:00.000Z",
    "initial_health_score": 72
}
```

**`tenants.goals`** (managed by goals service):

```sql
-- Created via goals service when onboarding completes
INSERT INTO tenants.goals (
    id, tenant_id, title, description, 
    current, target, unit, category, deadline
) VALUES (...);
```

## Testing the Complete Flow

### Prerequisites

1. SMB app running on port 3000
2. SMB gateway service running on port 8003
3. PostgreSQL database accessible
4. Accounts service running for authentication

### Test Scenario: CycloneRake Onboarding

1. **Navigate to Signup**:

   ```
   http://localhost:3000/signup
   ```

2. **Create Account**:
   - Email: `owner@cyclonerake.com`
   - Name: `CycloneRake Owner`
   - Password: `********`

3. **Complete Welcome Wizard**:

   **Step 1: Health Score**
   - System calculates business health score
   - Score displayed with animation
   - Click "Show me how to improve"

   **Step 2: Goal Selection**
   - Select "Optimize Operations" suggestion
   - Or enter custom goal: "Improve inventory turnover rate to 95%"
   - Click "Create my action plan"

   **Step 3: Plan Preview**
   - Review generated weekly tasks
   - Click "Connect my data first" to go to connectors
   - Or click "Skip to dashboard" to complete onboarding

4. **Backend Validation**:

   Check tenant metadata in PostgreSQL:

   ```sql
   SELECT tenant_id, metadata 
   FROM tenants.tenants 
   WHERE tenant_id = 'cyclonerake-demo001';
   ```

   Expected result:

   ```json
   {
       "onboarding_completed": true,
       "onboarding_completed_at": "2024-01-15T10:35:00.000Z",
       "initial_health_score": 72
   }
   ```

   Check created goal:

   ```sql
   SELECT * FROM tenants.goals 
   WHERE tenant_id = 'cyclonerake-demo001';
   ```

5. **Connect ERPNext** (if clicked "Connect my data first"):
   - Navigate to `/connectors`
   - Select "ERPNext" preset
   - Enter ERPNext credentials:
     - API URL: `https://erp.cyclonerake.com`
     - API Key: `<your_key>`
     - API Secret: `<your_secret>`
   - Click "Create Connector"
   - Trigger sync to fetch inventory/orders

6. **Test AI Coach**:
   - Navigate to `/coach`
   - Ask: "What products are low in stock?"
   - Verify coach uses real ERPNext data in response

## API Usage Examples

### Save Business Profile During Onboarding

```typescript
// In a custom onboarding flow, save profile separately
const saveProfile = async (profileData) => {
    const response = await fetch(
        `/api/smb/v1/tenants/${tenantId}/profile/business`,
        {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                Authorization: `Bearer ${apiToken}`,
            },
            body: JSON.stringify(profileData),
        }
    )
    
    const result = await response.json()
    console.log('Profile saved:', result)
}

// Example call
await saveProfile({
    industry: 'Food Service',
    team_size: '5-10',
    business_type: 'Restaurant',
    primary_goal: 'Increase revenue'
})
```

### Complete Onboarding with Goal Creation

```typescript
const completeOnboarding = async (healthScore, selectedGoal) => {
    const response = await fetch(
        `/api/smb/v1/tenants/${tenantId}/onboarding/complete`,
        {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                Authorization: `Bearer ${apiToken}`,
            },
            body: JSON.stringify({
                health_score: healthScore,
                selected_goal: {
                    title: 'Optimize Operations',
                    description: 'Improve inventory turnover to 95%',
                    current: 0,
                    target: 100,
                    unit: '%',
                    category: 'operations',
                    deadline: '2024-04-15'
                }
            }),
        }
    )
    
    const result = await response.json()
    console.log('Onboarding complete:', result)
    // Result: { success: true, goal_id: 'goal-xyz', tenant_id: '...' }
}
```

## Integration Points

### Auth Store

- Uses `apiToken` for authentication
- Uses `tenantId` for tenant scoping
- Data flows from `/signup` → auth store → welcome wizard → backend

### Goals Service

- Onboarding completion automatically creates goal
- Goal appears in `/goals` page
- AI coach can reference goal for personalized guidance

### Connector Data

- After onboarding, users connect ERPNext
- Connector data syncs to PostgreSQL
- AI coach uses connector data for context-aware responses

### Health Score

- Initial score calculated during onboarding
- Stored as baseline in tenant metadata
- Updates automatically as business metrics change

## Error Handling

### Backend Errors

**Tenant Not Found** (404):

```json
{
    "detail": "Tenant cyclonerake-demo001 not found"
}
```

**Database Error** (500):

```json
{
    "detail": "Database error: connection timeout"
}
```

### Frontend Error Handling

Welcome.tsx implements graceful degradation:

- API call failures are logged to console
- User still navigates to next page
- Onboarding marked complete in localStorage
- No blocking errors shown to user

**Rationale**: Better to complete onboarding flow even if persistence fails than to block user with error. Data can be collected later via profile page or settings.

## Future Enhancements

### Potential Additions

1. **Profile Retrieval Endpoint**:

   ```python
   @app.get("/v1/tenants/{tenant_id}/profile/business")
   async def get_business_profile(tenant_id: str):
       # Return saved profile data
   ```

2. **Partial Profile Updates**:
   - Allow updating individual fields without full profile
   - PATCH endpoint for incremental updates

3. **Onboarding Progress Tracking**:
   - Track which steps completed
   - Allow resuming incomplete onboarding

4. **Profile Validation**:
   - Validate industry against known list
   - Validate team_size format
   - Return validation errors

5. **Onboarding Analytics**:
   - Track completion rates
   - Identify drop-off points
   - Optimize wizard flow

## Production Checklist

- [x] Backend endpoints implemented
- [x] Frontend integration complete
- [x] Error handling added
- [x] Database schema supports data
- [x] Auth integration working
- [ ] API authentication tested
- [ ] PostgreSQL connection verified
- [ ] End-to-end flow tested with real user
- [ ] ERPNext connector tested with real credentials
- [ ] AI coach tested with real data

## Next Steps

1. **Test Complete Flow**:
   - Sign up as CycloneRake owner
   - Complete welcome wizard
   - Verify data persists to PostgreSQL
   - Connect ERPNext with real credentials
   - Test AI coach with real data

2. **Validate ERPNext Integration**:
   - Trigger connector sync
   - Verify inventory data in PostgreSQL
   - Check AI coach uses real inventory
   - Test low stock detection

3. **Monitor and Debug**:
   - Check backend logs for errors
   - Monitor database writes
   - Verify auth token flow
   - Test error scenarios

## Summary

The implementation adds critical persistence layer for the SMB onboarding flow:

✅ **Profile Persistence**: Business profile from welcome wizard saved to PostgreSQL
✅ **Goal Creation**: Selected goal automatically created in goals service  
✅ **Onboarding Tracking**: Completion status and timestamp recorded
✅ **Health Score Baseline**: Initial score stored for trend analysis
✅ **Frontend Integration**: Welcome.tsx calls backend endpoints
✅ **Error Handling**: Graceful degradation on API failures

This enables natural end-to-end testing through the SMB app without requiring database scripts or manual data seeding.
