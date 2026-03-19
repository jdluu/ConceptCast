# ConceptCast Monorepo Makefile
# Provides a unified interface for infrastructure, development, and maintenance.

.PHONY: \
	help \
	redis-up redis-down \
	setup update clean clean-dev \
	dev dev-backend dev-frontend dev-worker worker wait-for-backend gen-api \
	lint lint-frontend lint-backend \
	format format-frontend format-backend \
	typecheck typecheck-frontend typecheck-backend \
	build build-frontend build-backend \
	db-migrate db-generate db-status db-rollback \
	test-agents \
	e2e

# --- Common configuration ---

BACKEND_DIR := apps/backend
FRONTEND_FILTER := concept-cast-frontend
BACKEND_FILTER := backend
BASE_URL := http://localhost:8000

INFISICAL := infisical run --path=/ai --
BACKEND_SH := cd "$(BACKEND_DIR)" &&

# --- Help ---

help: ## Show this help message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# --- Infrastructure ---

redis-up: ## Start Redis container using Podman
	@if ! podman ps --format "{{.Names}}" | grep -q "^conceptcast-redis$$"; then \
		if podman ps -a --format "{{.Names}}" | grep -q "^conceptcast-redis$$"; then \
			echo "Starting existing Redis container..."; \
			podman start conceptcast-redis; \
		else \
			echo "Creating and starting new Redis container..."; \
			podman run -d --name conceptcast-redis -p 6379:6379 docker.io/library/redis:alpine; \
		fi; \
	else \
		echo "Redis container is already running."; \
	fi

redis-down: ## Stop Redis container
	@if podman ps --format "{{.Names}}" | grep -q "^conceptcast-redis$$"; then \
		echo "Stopping Redis container..."; \
		podman stop conceptcast-redis; \
	fi

# --- Setup & Maintenance ---

setup: ## Install all dependencies and run initial migrations
	@echo "Installing frontend dependencies..."
	pnpm install
	@echo "Installing backend dependencies..."
	$(BACKEND_SH) uv sync
	@$(MAKE) db-migrate

update: ## Update all dependencies to latest versions
	@echo "Updating frontend..."
	pnpm update
	@echo "Updating backend..."
	$(BACKEND_SH) uv sync --upgrade

clean: ## Remove build artifacts, node_modules, and virtual environments
	rm -rf node_modules
	rm -rf apps/*/node_modules
	rm -rf apps/backend/.venv
	rm -rf .turbo
	rm -rf apps/frontend/dist
	rm -rf apps/backend/e2e_reports/*.txt
	rm -rf apps/backend/e2e_reports/*.json

test-agents: ## Run agent intelligence and streaming diagnostics
	$(INFISICAL) bash -c '$(BACKEND_SH) uv run python src/scripts/test_agents.py'

# --- Development ---

wait-for-backend: ## Internal: Wait for backend to be ready
	@echo "Waiting for backend to be ready..."
	@until curl -s "$(BASE_URL)/openapi.json" > /dev/null; do sleep 1; done
	@echo "Backend is ready."

dev: redis-up ## Run full stack in dev mode with automatic API generation
	@if ss -ltn | rg -q ":8000[[:space:]]"; then \
		echo "Port 8000 is already in use (backend likely already running)."; \
		echo "Stop the existing backend process first, then run 'make dev'."; \
		echo "If you want to keep the current backend, run 'make dev-frontend' in another terminal."; \
		exit 1; \
	fi
	@$(INFISICAL) bash -lc 'set -euo pipefail; root_dir="$$(pwd)"; \
		backend_pid=""; worker_pid=""; \
		cleanup() { \
			trap - INT TERM EXIT; \
			echo "Shutting down full stack..."; \
			for pid in "$$worker_pid" "$$backend_pid"; do \
				if [ -n "$$pid" ] && kill -0 "$$pid" 2>/dev/null; then \
					kill -TERM -- "-$$pid" 2>/dev/null || kill -TERM "$$pid" 2>/dev/null || true; \
				fi; \
			done; \
			sleep 1; \
			for pid in "$$worker_pid" "$$backend_pid"; do \
				if [ -n "$$pid" ] && kill -0 "$$pid" 2>/dev/null; then \
					kill -KILL -- "-$$pid" 2>/dev/null || kill -KILL "$$pid" 2>/dev/null || true; \
				fi; \
			done; \
			wait "$$worker_pid" 2>/dev/null || true; \
			wait "$$backend_pid" 2>/dev/null || true; \
			cd "$$root_dir" && $(MAKE) -s redis-down; \
		}; \
		trap cleanup INT TERM EXIT; \
		setsid bash -lc "cd \"$(BACKEND_DIR)\" && uv run uvicorn main:app --app-dir src --reload --host 0.0.0.0 --port 8000" & backend_pid="$$!"; \
		$(MAKE) -s wait-for-backend; \
		$(MAKE) -s gen-api; \
		mkdir -p "$$root_dir/.cursor"; \
		setsid bash -lc "cd \"$(BACKEND_DIR)\" && uv run taskiq worker infra.tasks:broker --app-dir src" >"$$root_dir/.cursor/worker-dev.log" 2>&1 & worker_pid="$$!"; \
		set +e; \
		cd "apps/frontend" && ./node_modules/.bin/vite --host; status="$$?"; \
		set -e; \
		if [ "$$status" -eq 130 ] || [ "$$status" -eq 143 ]; then exit 0; fi; \
		exit "$$status"'

dev-backend: ## Run backend application only
	$(INFISICAL) pnpm turbo run dev --filter=$(BACKEND_FILTER)

dev-frontend: ## Run frontend application only
	$(INFISICAL) pnpm turbo run dev --filter=$(FRONTEND_FILTER)

dev-worker: ## Run background worker only
	$(INFISICAL) pnpm turbo run worker --filter=$(BACKEND_FILTER)

worker: dev-worker ## Alias for dev-worker

gen-api: ## Generate frontend API types from backend schema
	pnpm turbo run generate:api --filter=$(FRONTEND_FILTER)

# --- Quality & Build ---

lint: lint-frontend lint-backend ## Run all linters
lint-frontend: ## Run frontend linter (oxlint)
	pnpm turbo run lint --filter=$(FRONTEND_FILTER)
lint-backend: ## Run backend linter (ruff)
	pnpm turbo run lint --filter=$(BACKEND_FILTER)

format: format-frontend format-backend ## Run all formatters
format-frontend: ## Format frontend code (prettier)
	pnpm turbo run format --filter=$(FRONTEND_FILTER)
format-backend: ## Format backend code (ruff)
	$(BACKEND_SH) uv run ruff format .

typecheck: typecheck-frontend typecheck-backend ## Run all type checks
typecheck-frontend: ## Run frontend type check (tsc)
	pnpm turbo run typecheck --filter=$(FRONTEND_FILTER)
typecheck-backend: ## Run backend type check (mypy)
	$(BACKEND_SH) uv run mypy .

build: build-frontend build-backend ## Build all applications
build-frontend: ## Build frontend application
	pnpm turbo run build --filter=$(FRONTEND_FILTER)
build-backend: ## Build backend application
	pnpm turbo run build --filter=$(BACKEND_FILTER)

# --- Database Management (Backend) ---

db-migrate: ## Run pending database migrations
	@echo "Running backend migrations..."
	$(INFISICAL) bash -c '$(BACKEND_SH) uv run alembic upgrade head'

db-generate: ## Generate a new migration based on model changes
	@read -p "Enter migration message: " msg; \
	$(INFISICAL) bash -c '$(BACKEND_SH) uv run alembic revision --autogenerate -m "$$msg"'

db-status: ## Show current database migration status
	$(INFISICAL) bash -c '$(BACKEND_SH) uv run alembic current'

db-rollback: ## Roll back the last database migration
	$(INFISICAL) bash -c '$(BACKEND_SH) uv run alembic downgrade -1'

e2e: ## E2E runner. mode=one|suite (default one). Example: make e2e mode=one provider=nano model=openai/gpt-oss-120b topic="Large Language Models"
	@mode="$${mode:-one}"; \
	topic="$${topic:-Large Language Models}"; \
	audience="$${audience:-General Audience}"; \
	if [ "$$mode" = "suite" ]; then \
		$(INFISICAL) bash -c '$(BACKEND_SH) uv run python src/scripts/e2e_cli.py --topic "$$topic" --audience "$$audience"'; \
	else \
		provider="$${provider:-nano}"; \
		model="$${model:-openai/gpt-oss-120b}"; \
		hitl="$${hitl:-false}"; \
		$(INFISICAL) bash -c '$(BACKEND_SH) PYTHONPATH=src uv run python -c "import asyncio; from scripts.e2e_cli import run_single_simulation; result=asyncio.run(run_single_simulation('\''$$provider'\'','\''$$model'\'','\''$$topic'\'','\''$$audience'\'',hitl_enabled=(\x27$$hitl\x27==\x27true\x27))); print(result)"'; \
	fi

clean-dev: ## Dev cleanup: jobs, job artifacts, debug logs, and E2E reports
	@echo "Attempting DELETE /jobs on local backend (if running)..."
	@curl -fsS -X DELETE "$(BASE_URL)/jobs" >/dev/null 2>&1 || true
	@echo "Removing local job artifacts under data/jobs..."
	rm -rf data/jobs/*
	@echo "Removing debug logs and E2E reports..."
	rm -f .cursor/debug-*.log
	rm -rf apps/backend/e2e_reports/*.txt
	rm -rf apps/backend/e2e_reports/*.json
