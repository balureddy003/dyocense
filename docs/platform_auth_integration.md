# Platform Authentication Integration

## Overview

The Dyocense platform supports centralized authentication for all business tools and services. It uses Keycloak for identity management, with API token fallback for local/dev scenarios. Both backend and frontend are designed for multi-tenant, secure access.

## Backend (FastAPI)

- Keycloak credentials are loaded from environment variables.
- If Keycloak is unavailable, the service falls back to database-only authentication.
- All endpoints use the `require_auth` dependency to validate JWTs or API tokens.
- Tenant context is injected into every request for multi-tenant support.

### Example: Protecting an Endpoint

```python
from packages.kernel_common.deps import require_auth
from fastapi import Depends

@app.get("/v1/tenants/me")
def get_tenant_profile(identity: dict = Depends(require_auth)):
    # identity contains tenant_id, email, roles, etc.
    ...
```

## Frontend (React)

- `AuthContext.tsx` manages login, logout, and token storage.
- Supports Keycloak login and API token/manual login.
- Automatically hydrates user context from localStorage.
- Provides hooks for business tools to access user, tenant, and token info.

### Example: Using AuthContext

```tsx
import { useAuth } from '../context/AuthContext';

const { authenticated, user, login, logout } = useAuth();
```

## Multi-Tenant Support

- Tenant ID is always included in tokens and API calls.
- Onboarding flows provision tenants in Keycloak and send welcome emails.
- All business tools should use the tenant context for data isolation.

## Best Practices

- Always use `require_auth` in backend endpoints.
- Use `AuthContext` in frontend for all auth logic.
- Never hardcode tokens; use environment variables and secure storage.
- Document onboarding and login flows for new tools.

---
*This guide ensures consistent, secure authentication across the platform.*
