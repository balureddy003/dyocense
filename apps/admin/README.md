Dyocense — Admin (Keystone) scaffold

This folder contains a minimal Keystone 6 admin app for tenant/workspace/project management.

Quick start (macOS, zsh):

1. cd apps/admin
2. npm install
3. npm run dev

This starts Keystone on port 3001 and creates a local SQLite DB at `apps/admin/keystone.db`.

Notes:

- The schema includes `Tenant`, `Workspace`, `Project`, and `User` lists.
- In production you'll want PostgreSQL and proper auth/access control.
- To integrate with the main backend, expose REST/GraphQL endpoints or use Keystone as the primary source of truth and call its APIs from the FastAPI backend.
