SMB App — Minimal scaffold

This is a minimal Vite + React scaffold created as a focused place to build the SMB onboarding flow.

## Running locally

1. cd apps/smb
2. npm install
3. npm run dev

## Goals flow (inline wizard + versions)

The Goals page now includes an inline, AI‑assisted wizard for the first goal and lightweight version history for each goal. See `GOALS_FLOW.md` for details.

## API configuration

This app by default points to the local Keystone proxy at <http://localhost:8002>. You can configure the API host and proxy key using Vite env variables:

- VITE_API_BASE - base URL for API calls (default: <http://localhost:8002>)
- VITE_PROXY_API_KEY - optional x-api-key value to send with requests when the proxy is hardened

If you want me to switch to another backend host or wire up TanStack Query for caching, tell me or I can proceed.
