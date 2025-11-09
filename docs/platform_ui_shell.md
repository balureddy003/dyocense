# Platform UI Shell Integration

## Overview

The Dyocense platform UI shell is a React-based, extensible container for all business tools. It provides navigation, context sharing, and modular integration for analytics, onboarding, and future tool flows.

## Structure

- UI shell is implemented in `apps/ui/src/pages/App.tsx` and supporting components.
- Uses context providers (e.g., `AuthContext`) for authentication and user state.
- Navigation and tool registry are modular, allowing new tools to be added with minimal changes.

### Example: Adding a Tool to the Shell

```tsx
// In App.tsx or a registry file
import SalesInsightsFlow from '../components/SalesInsightsFlow';

const tools = [
  { name: 'Sales Insights', component: SalesInsightsFlow },
  // Add more tools here
];

// Render tools in navigation and main view
```

## Context Sharing

- All tools have access to shared context (auth, tenant, data) via React providers.
- Use hooks (e.g., `useAuth`) to access user and tenant info.

### Example: Accessing Context in a Tool

```tsx
import { useAuth } from '../context/AuthContext';

const { user, tenantId } = useAuth();
```

## Extensibility

- Add new tools as React components and register them in the shell.
- Use context providers for cross-tool communication and state.
- Document integration steps for each new tool.

## Best Practices

- Keep UI shell modular and decoupled from individual tools.
- Use context providers for all shared state.
- Document navigation and integration patterns for future tools.

---
*This guide ensures a scalable, modular UI shell for all platform business tools.*
