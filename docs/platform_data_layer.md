# Platform Data Layer Integration

## Overview

The Dyocense platform provides a unified data layer for all business tools, supporting both SQL and NoSQL backends. Data schemas are centralized in `packages/contracts/schemas/` and used for validation, transformation, and analytics.

## Backend (FastAPI)

- Import schemas from `contracts/schemas` for validation.
- Use shared models for all business objects (OPS, goalpack, catalog, etc.).
- Support for Cosmos DB, Postgres, and in-memory dev stores.
- Data access logic is modular and reusable across services.

### Example: Validating Data

```python
from contracts.schemas import ops
import jsonschema

def validate_ops(payload: dict):
    jsonschema.validate(instance=payload, schema=ops)
```

## Frontend (React)

- Import JSON schemas for client-side validation and mapping.
- Use Ajv or similar libraries for runtime validation.
- Data mapping and preview flows leverage shared schemas for consistency.

### Example: Client-Side Validation

```ts
import opsSchema from 'contracts/schemas/ops.schema.json';
import Ajv from 'ajv';

const ajv = new Ajv();
const validate = ajv.compile(opsSchema);
const valid = validate(payload);
```

## Extensibility

- Add new schemas to `contracts/schemas` for future business tools.
- Update API contracts and validation logic to support new data types.
- Use hierarchical partition keys and embedding for scalable data modeling (see Cosmos DB best practices).

## Best Practices

- Always validate data against shared schemas.
- Centralize schema updates and versioning.
- Use partition keys and hierarchical modeling for scalability.
- Document data flows for each business tool.

---
*This guide ensures a robust, extensible data layer for all platform tools.*
