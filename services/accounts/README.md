# Accounts Service

Manages Dyocense tenant registrations, subscription plans, and project catalogues. The service persists tenant metadata in MongoDB when available (falls back to in-memory collections for local development).

## Endpoints

- `GET /v1/plans` – list subscription plans and feature limits.
- `POST /v1/tenants/register` – public endpoint to provision a tenant, select a plan, and mint an API token.
- `GET /v1/tenants/me` – authenticated endpoint returning the caller's tenant profile and usage stats.
- `PUT /v1/tenants/me/subscription` – change subscription tier (authenticated).
- `POST /v1/projects` – create a project under the tenant, enforcing plan limits.
- `GET /v1/projects` – list projects for the authenticated tenant.
- `POST /v1/users/register` – create a password-based user inside a tenant (requires the tenant API token).
- `POST /v1/users/login` – exchange tenant ID, email, and password for a short-lived JWT.
- `GET /v1/users/me` – fetch the authenticated user's profile.
- `GET /v1/users/api-tokens` – list user-scoped API tokens.
- `POST /v1/users/api-tokens` – mint a new API token for the current user (the secret is returned once).
- `DELETE /v1/users/api-tokens/{token_id}` – revoke a user API token.

Authenticated routes expect a bearer token issued during tenant registration (or the existing `demo-` tokens used for local testing).
The user endpoints accept either a JWT produced by `/v1/users/login` or a user API token created via `/v1/users/api-tokens`.
