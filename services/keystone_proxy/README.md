Keystone Proxy
===============

This is a small FastAPI proxy that provides a simple REST surface for creating tenants,
workspaces, and projects in the Keystone admin GraphQL API. It also exposes a dev-friendly
`/v1/auth/verify` endpoint used by the SMB frontend for quick local onboarding.

Configuration
-------------

Set the following environment variables before running:

- KEYSTONE_GRAPHQL (optional) - URL of the Keystone GraphQL endpoint. Defaults to `http://localhost:3001/api/graphql`.
- PROXY_API_KEY (optional but recommended) - When set, the proxy will require the header `x-api-key: <PROXY_API_KEY>` for all endpoints.

Example .env

```
KEYSTONE_GRAPHQL=http://localhost:3001/api/graphql
PROXY_API_KEY=dev-secret-key
```

Frontend
--------

If you set PROXY_API_KEY, provide the same value to the SMB frontend via Vite env `VITE_PROXY_API_KEY` so the browser client can call the proxy endpoints:

VITE_PROXY_API_KEY=dev-secret-key

Run (development)
-----------------

Install dependencies into a virtualenv and run with uvicorn:

# create venv

python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# run server

uvicorn services.keystone_proxy.main:app --reload --host 127.0.0.1 --port 8002

Notes
-----

- This proxy is intentionally simple and intended for development and onboarding flows. For production, replace the dev `verify` implementation with your real auth provider and secure communications between services.
- The proxy will validate GraphQL responses and surface errors as HTTP 4xx/5xx responses.
