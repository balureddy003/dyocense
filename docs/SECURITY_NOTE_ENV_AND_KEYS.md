# Security Note: Environment Files and API Keys

This repository contains example environment files for local development. Never commit real credentials or long-lived secrets.

## Guidance

- Keep `.env` in `.gitignore` (already configured). Use `.env.example` as the template.
- Store real secrets in a secure location (1Password, Azure Key Vault, AWS Secrets Manager, etc.).
- Rotate any keys that were exposed in local files or logs.
- Prefer per-environment overrides (e.g., `.env.dev`, `.env.production`) with secrets only on the target machine.
- For asymmetric signatures:
  - Use `ENABLE_ASYMMETRIC_SIGNING=1` and `DEFAULT_SIGNATURE_MODE=auto|hmac|asymmetric` in non-sensitive env files.
  - Do not store private keys in the repo. For dev-only testing, `ED25519_PRIVATE_KEY_PEM` may be set locally—not committed.

## Recommended Actions

1. Replace real values in `.env` with placeholders and commit only the template (`.env.example`).
2. Rotate any API keys, SMTP app passwords, or tokens that may have been shared.
3. For production, prefer Key Vault/KMS for private key operations and application secrets.

## Example Template Excerpts

```dotenv
# Security
SECRET_KEY=change_me
JWT_SECRET=change_me

# Email (use provider key or app password securely)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=you@example.com
SMTP_PASS=your_app_password
SMTP_FROM="Dyocense <noreply@dyocense.com>"
SMTP_TLS=true

# AI
AZURE_OPENAI_ENDPOINT=https://your-endpoint.openai.azure.com
AZURE_OPENAI_API_KEY=your_azure_openai_key
AZURE_OPENAI_DEPLOYMENT=gpt-4o-mini

# Signing (Phase 3)
ENABLE_ASYMMETRIC_SIGNING=
DEFAULT_SIGNATURE_MODE=hmac
# ED25519_PRIVATE_KEY_PEM=-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----
```
