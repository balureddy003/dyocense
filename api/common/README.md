# Shared Service Toolkit

`api/common` packages reusable components for Dyocense services:

- **Kernel client** (`KernelClient`) with retry/backoff and typed DTOs.
- **Auth middleware** (`BearerAuthMiddleware`) that plugs into FastAPI/Starlette and populates tenant context.
- **Tenant context helpers** (`context.set_tenant`, `context.get_tenant`).
- **Tracing helpers** (`tracing.start_span`) with optional OpenTelemetry integration.
- **Mongo helpers** (`get_mongo_client`, `get_mongo_collection`).

## Installation

```bash
pip install -r api/requirements.txt
```

## Usage

```python
from api.common import KernelClient, KernelClientConfig

client = KernelClient(KernelClientConfig(base_url="http://localhost:8080"))
result = client.run_pipeline({"tenant_id": "tenant_demo", "goaldsl": {...}})
print(result.solution.kpis)
```

To customise auth, provide your own decoder:

```python
from api.common import BearerAuthMiddleware, AuthContext

async def decode_jwt(token: str) -> AuthContext:
    # TODO: verify signature, look up tenant tier
    return AuthContext(tenant_id="tenant_demo", tier="pro", token=token)

app.add_middleware(BearerAuthMiddleware, decoder=decode_jwt)
```

Tracing is optional; if `opentelemetry` is installed, spans are emitted automatically.
