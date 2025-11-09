
# Dyocense Shared Contracts & Schemas

This package centralizes all business contracts, schemas, and API specifications for the Dyocense platform. All microservices and UI components should import models and validation logic from here to ensure consistency and modularity.

## Contents

- **schemas/**: JSON schemas for business objects (catalog, goalpack, ops, plan, workspace, solution_pack)
- **openapi/**: OpenAPI specifications for platform APIs
- **mcp/**: Model Context Protocol (for agent workflows)
- ****init**.py**: Python entry point for importing schemas

## Usage Example (Python)

```python
from contracts.schemas import ops, catalog
import jsonschema

# Validate an OPS document
jsonschema.validate(instance=my_ops_doc, schema=ops)
```

## Usage Example (FastAPI Service)

```python
from contracts.schemas import goalpack
from fastapi import FastAPI, Body
import jsonschema

app = FastAPI()

@app.post('/v1/validate-goalpack')
def validate_goalpack(payload: dict = Body(...)):
 jsonschema.validate(instance=payload, schema=goalpack)
 return {"status": "valid"}
```

## Usage Example (Frontend)

```ts
// Use schemas for client-side validation
import goalpackSchema from 'contracts/schemas/goalpack.schema.json';
import Ajv from 'ajv';

const ajv = new Ajv();
const validate = ajv.compile(goalpackSchema);
const valid = validate(payload);
```

## Best Practices

- Always import schemas from this package, never duplicate models.
- Update schemas here before adding new business logic or endpoints.
- Use OpenAPI specs for API contract-first development.

## Validation

Use the root `make validate` command (or run `python scripts/validate_ops.py`) to validate example payloads against the OPS schema. As additional schemas are introduced, extend the script and add new make targets.

---
*This package is the foundation for platform modularity and tool extensibility.*
