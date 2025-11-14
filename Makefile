PYTHON ?= python3
VENV = .venv
VENV_BIN = $(VENV)/bin

.PHONY: validate format lint setup install clean test run-kernel run-compiler run-optimiser run-forecast run-explainer run-policy run-diagnostician run-evidence run-marketplace run-orchestrator kind-up capture-trip-planner setup-browsers

$(VENV):
	$(PYTHON) -m venv $(VENV)

setup: $(VENV)
ifeq ($(SKIP_PIP),1)
	@echo "Skipping dependency installation (SKIP_PIP=1)."
else
	$(VENV_BIN)/pip install -r requirements-dev.txt
endif

clean:
	rm -rf $(VENV)
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

validate: setup
	$(VENV_BIN)/python scripts/validate_ops.py examples/inventory_simple.ops.json

lint:
	@echo "Linting is not yet configured. Enable in Phase 2."

format:
	@echo "Formatting is not yet configured. Enable in Phase 2."

test: setup
	PYTHONPATH=. $(VENV_BIN)/pytest

# =================================================================
# v4.0 Unified Backend Commands
# =================================================================

dev: setup
	@echo "Starting Dyocense v4.0 backend..."
	PYTHONPATH=. $(VENV_BIN)/uvicorn backend.main:app --reload --host 127.0.0.1 --port 8001 --log-level debug

run-backend: dev

migrate: setup
	@echo "Running database migrations..."
	PYTHONPATH=. $(VENV_BIN)/alembic upgrade head

migrate-create: setup
	@echo "Creating new migration..."
	@read -p "Migration name: " name; \
	PYTHONPATH=. $(VENV_BIN)/alembic revision --autogenerate -m "$$name"

migrate-rollback: setup
	@echo "Rolling back last migration..."
	PYTHONPATH=. $(VENV_BIN)/alembic downgrade -1

db-shell: setup
	@echo "Connecting to PostgreSQL..."
	psql postgresql://dyocense:dyocense@localhost:5432/dyocense

# =================================================================
# Legacy Service Commands (for migration reference)
# =================================================================

run-kernel: setup
	PYTHONPATH=. $(VENV_BIN)/uvicorn services.kernel.main:app --reload --port 8001


run-compiler: setup
	PYTHONPATH=. $(VENV_BIN)/uvicorn services.compiler.main:app --reload --port 8002

run-optimiser: setup
	PYTHONPATH=. $(VENV_BIN)/uvicorn services.optimiser.main:app --reload --port 8003

run-forecast: setup
	PYTHONPATH=. $(VENV_BIN)/uvicorn services.forecast.main:app --reload --port 8004

run-explainer: setup
	PYTHONPATH=. $(VENV_BIN)/uvicorn services.explainer.main:app --reload --port 8005

run-policy: setup
	PYTHONPATH=. $(VENV_BIN)/uvicorn services.policy.main:app --reload --port 8006

run-diagnostician: setup
	PYTHONPATH=. $(VENV_BIN)/uvicorn services.diagnostician.main:app --reload --port 8007

run-evidence: setup
	PYTHONPATH=. $(VENV_BIN)/uvicorn services.evidence.main:app --reload --port 8008

run-marketplace: setup
	PYTHONPATH=. $(VENV_BIN)/uvicorn services.marketplace.main:app --reload --port 8009

run-orchestrator: setup
	PYTHONPATH=. $(VENV_BIN)/uvicorn services.orchestrator.main:app --reload --port 8010

kind-up:
	bash scripts/kind_bootstrap.sh

# Install Playwright browsers (one-time) for recording scripts
setup-browsers: setup
	$(VENV_BIN)/python -m playwright install --with-deps

# Capture a live Trip.com planner session: video, screenshots, and a trace
ARGS ?=

capture-trip-planner: setup
	PYTHONPATH=. $(VENV_BIN)/python scripts/capture_trip_planner.py $(ARGS)
