# Simple Local Setup (Postgres Stack)

Use this guide when you just want the services running locally with the new Postgres-backed repositories, without reading every historical doc. Follow the sections in order; each builds on the previous one.

---

## 1. Requirements

- macOS/Linux with Docker Desktop (or Docker Engine) and Compose v2
- Python 3.11 (matches `requirements-dev.txt`)
- `pip` and `virtualenv` (or `pyenv`, `uv`, etc.)
- `psql` (optional but handy for verifying the database)

---

## 2. One-Time Project Setup

```bash
git clone https://github.com/<org>/dyocense.git
cd dyocense

# Create a virtual environment (feel free to swap for pyenv/uv/poetry)
python3.11 -m venv .venv
source .venv/bin/activate

# Install all Python dependencies
pip install -r requirements-dev.txt

# Copy an env file and update secrets/URLs as needed
cp .env.example .env
```

Minimal env vars you must set in `.env` (or export manually):

```
POSTGRES_URL=postgresql://metadata:metadataPass123@localhost:5432/metadata
ALLOW_ANONYMOUS=true            # optional: simplifies local auth
```

---

## 3. Start Postgres (with pgvector ready)

We ship a Compose service that now uses the pgvector-enabled image, so no manual extension install is required.

```bash
# Build (installs pgvector extension) and start Postgres
docker compose -f infra/docker-compose/docker-compose.yaml build postgres-metadata
docker compose -f infra/docker-compose/docker-compose.yaml up -d postgres-metadata

# Tail logs (optional)
docker compose -f infra/docker-compose/docker-compose.yaml logs -f postgres-metadata
```

The container exposes `localhost:5432` with:

- user: `metadata`
- password: `metadataPass123`
- database: `metadata`

Feel free to change these in the Compose file if you prefer different credentials—just keep `POSTGRES_URL` in sync.

---

## 4. Initialize the Schema

```bash
source .venv/bin/activate
export POSTGRES_URL="postgresql://metadata:metadataPass123@localhost:5432/metadata"
python scripts/run_migration.py infra/postgres/migrations/001_full_schema.sql
```

This single SQL file mirrors `infra/postgres/schema.sql`, so you get the tenants, connectors, evidence, trust, and versioning tables in one shot. Re-run it any time you drop the database.

---

## 5. Run a Service

Example: start the Accounts API on port 8002.

```bash
PYTHONPATH=. uvicorn services.accounts.main:app --reload --port 8002
```

Other frequently used services:

| Service          | Command                                                                    | Notes                                   |
|------------------|----------------------------------------------------------------------------|-----------------------------------------|
| Kernel API       | `PYTHONPATH=. uvicorn services.kernel.main:app --reload --port 8001`       | Unified router: accounts, connectors, gateway, legacy endpoints |

Hit `http://localhost:<port>/docs` to explore each FastAPI surface.

> **Note:** Kernel now mounts the Accounts, Connectors, and SMB Gateway routers, so `services.kernel.main` is the only process you normally need to run. Spin up individual services only when you want to debug them in isolation.

---

## 6. Making Code or Schema Changes

### Code changes
1. Make your edits.
2. (Optional) run focused tests, e.g. `pytest tests/test_erpnext_connector.py`.
3. Restart whichever `uvicorn` service you are running so it picks up the changes.

### Schema changes
1. Update `infra/postgres/schema.sql` with the desired tables/columns/indexes.
2. Create a new numbered migration so teammates don't have to reapply the whole schema:
   ```bash
   cp infra/postgres/migrations/001_full_schema.sql infra/postgres/migrations/002_<short_name>.sql
   # Edit the new file so it only contains the new statements.
   ```
3. Run it:
   ```bash
   python scripts/run_migration.py infra/postgres/migrations/002_<short_name>.sql
   ```
4. Commit both the schema change and the new migration file.

When you pull new changes, rerun any migrations that appeared in the PR history. They are always stored in `infra/postgres/migrations/`.

---

## 7. Resetting From Scratch

```bash
docker compose -f infra/docker-compose/docker-compose.yaml down -v   # wipes the DB volume
docker compose -f infra/docker-compose/docker-compose.yaml up -d postgres-metadata
python scripts/run_migration.py infra/postgres/migrations/001_full_schema.sql
```

That gives you a clean Postgres plus the baseline schema in under a minute.

---

## 8. Troubleshooting Cheatsheet

| Symptom | Fix |
|--------|-----|
| `extension "vector" is not available` | Rebuild the `postgres-metadata` container so it uses the bundled pgvector image: `docker compose -f infra/docker-compose/docker-compose.yaml build postgres-metadata && docker compose -f infra/docker-compose/docker-compose.yaml up -d postgres-metadata`. |
| `POSTGRES_URL environment variable not set` | `export POSTGRES_URL=postgresql://<user>:<pass>@localhost:5432/<db>` before running migrations or services. |
| `psycopg2.OperationalError` about connection refused | Verify the container is up: `docker compose ... ps`. If the port is in use, stop the conflicting Postgres instance or change the host port. |
| FastAPI cannot start due to missing tables | Run the migration command again; the files are idempotent for existing objects. |

---

## 9. Next Steps

- Seed data for demos: `python scripts/seed_cyclonerake_tasks.py` (requires the gateway service).
- Run UI: `npm install && npm run dev --workspace apps/smb`.
- Automate migrations in CI/CD: add `python scripts/run_migration.py infra/postgres/migrations/<latest>.sql` to your deploy workflow.

Refer back to this document whenever you need the high-level flow; deeper architectural docs remain in `docs/` if you want the full story later.
