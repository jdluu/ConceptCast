# ConceptCast Monorepo Makefile
# Provides a unified interface for infrastructure, development, and maintenance.

.PHONY: help setup update dev dev-backend dev-frontend dev-worker db-migrate db-generate db-status db-rollback lint format build clean redis-up redis-down

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
	cd apps/backend && uv sync
	@make db-migrate

update: ## Update all dependencies to latest versions
	@echo "Updating frontend..."
	pnpm update
	@echo "Updating backend..."
	cd apps/backend && uv sync --upgrade

clean: ## Remove build artifacts, node_modules, and virtual environments
	rm -rf node_modules
	rm -rf apps/*/node_modules
	rm -rf apps/backend/.venv
	rm -rf .turbo
	rm -rf apps/frontend/dist

# --- Development ---

wait-for-backend: ## Internal: Wait for backend to be ready
	@echo "Waiting for backend to be ready..."
	@until curl -s http://localhost:8000/openapi.json > /dev/null; do sleep 1; done
	@echo "Backend is ready."

dev: redis-up ## Run full stack in dev mode with automatic API generation
	@trap 'make redis-down' SIGINT SIGTERM; \
	(make wait-for-backend && make gen-api &); \
	infisical run --path=/ai -- pnpm turbo run dev worker

dev-backend: ## Run backend application only
	infisical run --path=/ai -- pnpm turbo run dev --filter=backend

dev-frontend: ## Run frontend application only
	infisical run --path=/ai -- pnpm turbo run dev --filter=concept-cast-frontend

dev-worker: ## Run background worker only
	infisical run --path=/ai -- pnpm turbo run worker --filter=backend

worker: dev-worker ## Alias for dev-worker

gen-api: ## Generate frontend API types from backend schema
	infisical run --path=/ai -- pnpm turbo run generate:api --filter=concept-cast-frontend

# --- Quality & Build ---

lint: lint-frontend lint-backend ## Run all linters
lint-frontend: ## Run frontend linter (oxlint)
	pnpm turbo run lint --filter=concept-cast-frontend
lint-backend: ## Run backend linter (ruff)
	pnpm turbo run lint --filter=backend

format: format-frontend format-backend ## Run all formatters
format-frontend: ## Format frontend code (prettier)
	pnpm turbo run format --filter=concept-cast-frontend
format-backend: ## Format backend code (ruff)
	cd apps/backend && uv run ruff format .

typecheck: typecheck-frontend typecheck-backend ## Run all type checks
typecheck-frontend: ## Run frontend type check (tsc)
	pnpm turbo run typecheck --filter=concept-cast-frontend
typecheck-backend: ## Run backend type check (mypy)
	cd apps/backend && uv run mypy .

build: build-frontend build-backend ## Build all applications
build-frontend: ## Build frontend application
	pnpm turbo run build --filter=concept-cast-frontend
build-backend: ## Build backend application
	pnpm turbo run build --filter=backend

# --- Database Management (Backend) ---

db-migrate: ## Run pending database migrations
	@echo "Running backend migrations..."
	infisical run --path=/ai -- bash -c "cd apps/backend && uv run alembic upgrade head"

db-generate: ## Generate a new migration based on model changes
	@read -p "Enter migration message: " msg; \
	infisical run --path=/ai -- bash -c "cd apps/backend && uv run alembic revision --autogenerate -m \"$$msg\""

db-status: ## Show current database migration status
	infisical run --path=/ai -- bash -c "cd apps/backend && uv run alembic current"

db-rollback: ## Roll back the last database migration
	infisical run --path=/ai -- bash -c "cd apps/backend && uv run alembic downgrade -1"

e2e-cli: ## Run E2E simulation across all models (usage: make e2e-cli msg="Your Topic")
	@if [ -z "$(msg)" ]; then echo "Error: Missing msg parameter. Example: make e2e-cli msg=\"Explain React\""; exit 1; fi
	infisical run --path=/ai -- bash -c "cd apps/backend && uv run python src/scripts/e2e_cli.py --topic '$(msg)'"
