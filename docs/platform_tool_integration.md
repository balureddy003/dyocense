# Platform Tool Integration Guide

## Overview

This guide describes how to add new business tools to the Dyocense platform, leveraging shared services, authentication, data layer, UI shell, and API gateway.

## Step-by-Step Integration

1. **Define Data Schema**
   - Add new JSON schema to `packages/contracts/schemas/` for your tool’s data model.
   - Update OpenAPI contract if new endpoints are needed.

2. **Backend Service**
   - Create a new microservice in `services/` or extend an existing one.
   - Import shared contracts and validation logic.
   - Implement endpoints matching the OpenAPI spec.
   - Use `require_auth` for secure, multi-tenant access.

3. **Frontend Component**
   - Build a React component in `apps/ui/src/components/` for your tool.
   - Register the tool in the UI shell (e.g., add to navigation in `App.tsx`).
   - Use context providers for auth, tenant, and shared state.
   - Validate data using shared schemas (Ajv, etc.).

4. **API Integration**
   - Connect frontend to backend endpoints via REST or GraphQL.
   - Use shared API contracts for request/response validation.

5. **Testing & Documentation**
   - Add unit and integration tests for backend and frontend.
   - Document tool usage, onboarding, and integration steps in `docs/`.

## Example: Adding a Data Mapping Assistant

- Define `data_mapping.schema.json` in `contracts/schemas/`.
- Create `services/data_mapping/main.py` for backend logic.
- Build `DataMappingAssistant.tsx` in `components/`.
- Register in UI shell and connect to backend endpoint.
- Document integration in `docs/platform_tool_integration.md`.

## Best Practices

- Always use shared contracts and context providers.
- Validate all data and API flows.
- Document integration steps for future maintainers.

---
*This guide ensures rapid, consistent integration of new business tools on the platform.*
