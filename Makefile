# PAEOS-FX developer tasks. Run `make help` for the list.

BACKEND := backend
VENV := $(BACKEND)/.venv
PY := $(VENV)/bin/python
PIP := $(VENV)/bin/pip

.PHONY: help
help:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) \
		| awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2}'

.PHONY: venv
venv: ## Create the backend virtualenv and install dev deps
	python3 -m venv $(VENV)
	$(PIP) install --upgrade pip
	$(PIP) install -e "$(BACKEND)[dev]"

.PHONY: test
test: ## Run the test suite (unit; DB tests skip without PAEOS_TEST_DATABASE_URL)
	cd $(BACKEND) && .venv/bin/pytest

.PHONY: lint
lint: ## Run ruff lint
	cd $(BACKEND) && .venv/bin/ruff check .

.PHONY: format
format: ## Auto-format with ruff
	cd $(BACKEND) && .venv/bin/ruff format . && .venv/bin/ruff check --fix .

.PHONY: typecheck
typecheck: ## Run mypy
	cd $(BACKEND) && .venv/bin/mypy paeos_fx

.PHONY: migrate
migrate: ## Apply database migrations (requires a live PostgreSQL+PostGIS)
	cd $(BACKEND) && .venv/bin/alembic upgrade head

.PHONY: run
run: ## Run the API locally
	cd $(BACKEND) && .venv/bin/uvicorn paeos_fx.main:app --reload

.PHONY: up
up: ## Start the full dev stack in Docker
	cd infra && docker compose up --build

.PHONY: down
down: ## Stop the dev stack
	cd infra && docker compose down

.PHONY: check
check: lint typecheck test ## Run lint + typecheck + tests
