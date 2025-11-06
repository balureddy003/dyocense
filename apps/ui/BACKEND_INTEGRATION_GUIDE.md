# Backend Integration Guide

## API Changes Needed

### 1. Update Tenant Profile Endpoint

**Current:** `GET /v1/tenants/me`
```json
{
  "tenant_id": "...",
  "name": "Joe's Restaurant",
  "owner_email": "...",
  "plan": {...},
  "status": "active",
  "usage": {...},
  "metadata": {}  // Currently empty
}
```

**Enhanced:** Add business profile to metadata
```json
{
  "tenant_id": "...",
  "name": "Joe's Restaurant",
  "owner_email": "...",
  "plan": {...},
  "status": "active",
  "usage": {...},
  "metadata": {
    "business_profile": {
      "business_type": "Restaurant",
      "objectives": ["Reduce Cost", "Improve Service"],
      "operating_pace": "Pilot-first",
      "budget": "Lean",
      "markets": ["Local"],
      "other_needs": "30-seat restaurant, seasonal menu",
      "last_updated": "2025-11-06T11:30:00Z"
    }
  }
}
```

### 2. Create/Update Profile Endpoint

**Endpoint:** `PUT /v1/tenants/me/profile`

**Request Body:**
```json
{
  "business_type": "Restaurant",
  "objectives": ["Reduce Cost", "Improve Service"],
  "operating_pace": "Pilot-first",
  "budget": "Lean",
  "markets": ["Local"],
  "other_needs": "30-seat restaurant, seasonal menu"
}
```

**Response:**
```json
{
  "message": "Business profile updated successfully",
  "profile": {
    "tenant_id": "...",
    "name": "Joe's Restaurant",
    "metadata": {
      "business_profile": {
        // ... updated profile
      }
    }
  }
}
```

**Implementation (Python FastAPI):**
```python
from pydantic import BaseModel
from typing import List, Optional

class BusinessProfileUpdate(BaseModel):
    business_type: Optional[str] = None
    objectives: Optional[List[str]] = None
    operating_pace: Optional[str] = None
    budget: Optional[str] = None
    markets: Optional[List[str]] = None
    other_needs: Optional[str] = None

@app.put("/v1/tenants/me/profile")
async def update_business_profile(
    profile: BusinessProfileUpdate,
    tenant_id: str = Depends(get_current_tenant_id)
):
    # Get existing tenant
    tenant = await get_tenant(tenant_id)
    
    # Update metadata.business_profile
    if "business_profile" not in tenant.metadata:
        tenant.metadata["business_profile"] = {}
    
    business_profile = tenant.metadata["business_profile"]
    
    if profile.business_type:
        business_profile["business_type"] = profile.business_type
    if profile.objectives:
        business_profile["objectives"] = profile.objectives
    if profile.operating_pace:
        business_profile["operating_pace"] = profile.operating_pace
    if profile.budget:
        business_profile["budget"] = profile.budget
    if profile.markets:
        business_profile["markets"] = profile.markets
    if profile.other_needs is not None:
        business_profile["other_needs"] = profile.other_needs
    
    business_profile["last_updated"] = datetime.utcnow().isoformat()
    
    # Save tenant
    await update_tenant(tenant_id, tenant)
    
    return {
        "message": "Business profile updated successfully",
        "profile": tenant
    }
```

## 3. Goal Recommendations Endpoint (Optional Enhancement)

**Endpoint:** `GET /v1/goals/suggestions`

**Query Parameters:**
- `business_type`: string (e.g., "Restaurant")
- `objectives`: comma-separated (e.g., "Reduce Cost,Improve Service")
- `pace`: string (e.g., "Pilot-first")
- `budget`: string (e.g., "Lean")

**Response:**
```json
{
  "suggestions": [
    {
      "id": "rest-cost-1",
      "title": "Optimize Inventory Management",
      "description": "Reduce food waste by 40%...",
      "rationale": "Restaurants waste 4-10%...",
      "icon": "📦",
      "priority": "high",
      "estimated_duration": "4-6 weeks",
      "expected_impact": "15-20% cost reduction",
      "template_id": "inventory-optimization-restaurant"
    }
  ],
  "count": 5
}
```

## Database Schema Changes

### MongoDB/Firestore (if used)
```javascript
// tenants collection
{
  _id: "tenant_123",
  name: "Joe's Restaurant",
  // ... existing fields
  metadata: {
    business_profile: {
      business_type: "Restaurant",
      objectives: ["Reduce Cost", "Improve Service"],
      operating_pace: "Pilot-first",
      budget: "Lean",
      markets: ["Local"],
      other_needs: "30-seat restaurant",
      last_updated: ISODate("2025-11-06T11:30:00Z")
    }
  }
}
```

### PostgreSQL (if used)
```sql
-- Add JSONB column to tenants table
ALTER TABLE tenants 
ADD COLUMN business_profile JSONB DEFAULT '{}';

-- Index for queries
CREATE INDEX idx_tenants_business_type 
ON tenants ((business_profile->>'business_type'));

-- Example query
SELECT * FROM tenants 
WHERE business_profile->>'business_type' = 'Restaurant'
  AND business_profile->'objectives' @> '["Reduce Cost"]';
```

## Frontend Already Handles:

✅ Auto-detection of business type from tenant name
✅ Smart budget defaults from plan tier  
✅ Goal template library (60+ templates)
✅ Preference modal UI
✅ Goal suggestions display

## Backend Should Add (Priority Order):

### P0 (Must Have)
1. ✅ `PUT /v1/tenants/me/profile` - Save preferences
2. ✅ Load saved preferences in `GET /v1/tenants/me`

### P1 (Should Have)
3. Track preference changes (analytics)
4. Track which goals users select (analytics)

### P2 (Nice to Have)
5. `GET /v1/goals/suggestions` - Server-side goal generation
6. Industry benchmarks API
7. Goal template customization per tenant

## Testing Checklist

- [ ] Save preferences → reload page → preferences persist
- [ ] Update preferences → old values replaced
- [ ] Invalid business_type → validation error
- [ ] Missing tenant → 404 error
- [ ] Unauthenticated request → 401 error
- [ ] Metadata field backwards compatible (existing tenants work)

## Migration Strategy

### Step 1: Add metadata field
```python
# Ensure all existing tenants have metadata field
for tenant in get_all_tenants():
    if not hasattr(tenant, 'metadata'):
        tenant.metadata = {}
        update_tenant(tenant.tenant_id, tenant)
```

### Step 2: Deploy backend changes
- Add `PUT /v1/tenants/me/profile` endpoint
- Update `GET /v1/tenants/me` to include metadata

### Step 3: Frontend already deployed ✅
- Preferences modal works with or without backend
- Falls back to frontend-only state if API not available

### Step 4: Add analytics (optional)
- Track preference selections
- Track goal selections
- Generate insights for product team

## Security Considerations

1. **Validation:** Ensure business_type is from allowed list
2. **Authorization:** Only tenant owner can update profile
3. **Rate Limiting:** Prevent abuse of profile updates
4. **Sanitization:** Clean other_needs field (user input)

## Example cURL Requests

```bash
# Get tenant profile
curl -X GET http://localhost:8000/v1/tenants/me \
  -H "Authorization: Bearer $TOKEN"

# Update business profile
curl -X PUT http://localhost:8000/v1/tenants/me/profile \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "business_type": "Restaurant",
    "objectives": ["Reduce Cost", "Improve Service"],
    "operating_pace": "Pilot-first",
    "budget": "Lean",
    "markets": ["Local"],
    "other_needs": "30-seat restaurant, seasonal menu"
  }'
```

## Rollout Plan

### Week 1: Backend Only
- Deploy `PUT /v1/tenants/me/profile` endpoint
- Test with Postman/cURL
- Monitor errors

### Week 2: Frontend Integration
- Connect preference modal to API
- Test save/load flow
- Monitor analytics

### Week 3: Optimization
- Add goal suggestions API (optional)
- Tune performance
- Gather user feedback

## Questions for Backend Team

1. **Storage:** MongoDB, PostgreSQL, or other?
2. **Auth:** How to get current tenant_id from JWT?
3. **Validation:** Any business rules for allowed values?
4. **Analytics:** Should we log preference changes?
5. **Timeline:** When can this be deployed?

## Support Contact

Frontend: [Your Name]
Backend: [Backend Dev Name]
Product: [PM Name]
