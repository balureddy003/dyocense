# Platform API Gateway Integration

## Overview

The Dyocense platform API gateway standardizes communication between business tools, microservices, and the UI. It uses OpenAPI contracts for REST endpoints and supports future GraphQL extensions.

## Structure

- API contracts are defined in `packages/contracts/openapi/` (e.g., `decision-kernel.yaml`).
- Microservices expose endpoints matching these contracts.
- The gateway can be implemented via FastAPI, API Gateway, or reverse proxy.

### Example: Defining an Endpoint

```yaml
# In decision-kernel.yaml
/v1/compile:
  post:
    summary: Compile goal into an OPS document
    requestBody:
      required: true
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/CompileRequest'
    responses:
      '200':
        description: Successful compilation
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/CompileResponse'
```

## Best Practices

- Always use OpenAPI contracts for endpoint design.
- Validate requests and responses against shared schemas.
- Document all endpoints and flows for business tools.
- Plan for future GraphQL or event-driven extensions.

---
*This guide ensures standardized, contract-driven API integration for all platform tools.*
