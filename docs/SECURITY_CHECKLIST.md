# Security Checklist (Phase-1)

This repo contains configuration and code that can run locally and in the cloud. Use this checklist to reduce risk.

## 1) Secrets hygiene

- Never commit real secrets. Replace `.env` with `.env.local` (git-ignored) and add `.env.example` with placeholders.
- Rotate the following if ever committed/shared:
  - SMTP_PASS / SMTP credentials
  - SECRET_KEY / JWT_SECRET / ACCOUNTS_JWT_SECRET
  - AZURE_OPENAI_API_KEY / any model provider keys
  - CONNECTOR_ENCRYPTION_KEY (and re-encrypt stored credentials)
- Prefer a secret manager in non-dev environments:
  - Azure Key Vault, AWS Secrets Manager, or HashiCorp Vault

## 2) Email configuration

- Use provider API keys (e.g., SendGrid) or app passwords with least privilege.
- Verify “from” domains and SPF/DKIM.

## 3) Data at rest

- Encrypt connector credentials with envelope encryption and tenant-derived subkeys.
- Store only what you need (minimize PII). Anonymize where possible.

## 4) Logs and telemetry

- Scrub PII and secrets from logs.
- Use sampling for chat/content logs; provide opt-out.

## 5) Access control

- Scope tokens per environment (dev/stage/prod) and per tenant when feasible.
- Enforce CORS and auth on admin endpoints.

## 6) Decision ledger integrity (Phase-2+)

- Move from HMAC to per-tenant asymmetric keys.
- Add chain verification endpoint and periodic audits.

## 7) Rotation playbooks

- Document rotation steps for each secret. Automate via CI/CD where possible.
