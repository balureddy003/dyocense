## Dyocense Experience UI

This Vite + React workspace powers the Dyocense decision operating system shell. The latest update introduces:

- A marketing-focused landing funnel with clear navigation to either sign in or purchase the platform.
- Keycloak-based authentication (for enterprise SSO) plus first-party email/password login for small tenants.
- A guided post-login flow that captures business profile context and lets users mint personal API tokens.

### Environment variables

Create a `.env` file (or update your existing one) inside `apps/ui` with:

```bash
VITE_KEYCLOAK_URL=https://<keycloak-host>/auth
VITE_KEYCLOAK_REALM=<realm>
VITE_KEYCLOAK_CLIENT_ID=<public-client-id>
VITE_DYOCENSE_BASE_URL=http://localhost:8001
```

If the Keycloak variables are omitted, users can authenticate with tenant ID + API token or the email/password flow. Demo mode remains available for quick previews.

### Development

```bash
cd apps/ui
npm install
npm run dev
```

The marketing site renders at `http://localhost:5173/`, and protected routes (e.g. `/home`) redirect through the Keycloak login unless you are in mock mode.
