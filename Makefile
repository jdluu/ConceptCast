# ConceptCast Monorepo Makefile
# Provides a unified interface for infrastructure, development, and maintenance.

.PHONY: \
	help \
	setup update clean \
	dev dev-backend dev-frontend dev-worker \
	wait-for-backend gen-api \
	lint lint-frontend lint-backend \
	format format-frontend format-backend \
	typecheck typecheck-frontend typecheck-backend \
	test test-backend test-agents e2e \
	build build-frontend build-backend \
	db-migrate db-generate db-status db-rollback \
	redis-up redis-down

# --- Common configuration ---

BACKEND_DIR := apps/backend
FRONTEND_FILTER := concept-cast-frontend
BACKEND_FILTER := backend
BASE_URL := http://localhost:8000

# Container engine detection (Podman preferred, Docker fallback)
CONTAINER_TOOL := $(shell which podman 2>/dev/null || which docker 2>/dev/null)
ifeq ($(CONTAINER_TOOL),)
$(warning "No container engine (podman or docker) found. Redis will not be started automatically.")
endif

# Infisical configuration (can be bypassed with USE_INFISICAL=false)
USE_INFISICAL ?= true
INFISICAL_PATH ?= /ConceptCast
INFISICAL_ENV ?= dev
INFISICAL_PROJECT_ID ?= b5af8dff-e2cd-492a-bf10-a71ce71deb58
INFISICAL :=

# Token helper: machine-identity token via BWS-stored credentials.
# Falls back gracefully when either BWS or Infisical is unavailable.
INFISICAL_TOKEN_HELPER ?= $(CURDIR)/scripts/infisical-token.sh

ifeq ($(USE_INFISICAL),true)
    # Check if infisical CLI is installed
    HAS_INFISICAL := $(shell which infisical 2>/dev/null)
    ifneq ($(HAS_INFISICAL),)
        # Machine identity auth: fetch token, then verify the configured path works.
        INFISICAL_TOKEN := $(shell bash $(INFISICAL_TOKEN_HELPER) 2>/dev/null)
        ifneq ($(INFISICAL_TOKEN),)
            INFISICAL_WORKS := $(shell INFISICAL_TOKEN="$(INFISICAL_TOKEN)" infisical run --projectId $(INFISICAL_PROJECT_ID) --env=$(INFISICAL_ENV) --path=$(INFISICAL_PATH) -- true >/dev/null 2>&1 && echo "ok" || echo "fail")
            ifeq ($(INFISICAL_WORKS),ok)
                INFISICAL := env INFISICAL_TOKEN="$(INFISICAL_TOKEN)" infisical run --projectId $(INFISICAL_PROJECT_ID) --env=$(INFISICAL_ENV) --path=$(INFISICAL_PATH) --
            else
                $(warning "Infisical auth OK but path '$(INFISICAL_PATH)' in environment '$(INFISICAL_ENV)' is inaccessible. Falling back to local environment.")
                INFISICAL :=
            endif
        else
            $(warning "Could not fetch an Infisical machine-identity token (BWS unavailable?). Falling back to local environment.")
            INFISICAL :=
        endif
    endif
endif

BACKEND_SH := cd "$(BACKEND_DIR)" &&

# --- Help ---

help: ## Show this help message
	@printf "\033[1mConceptCast Management Commands\033[0m\n\n"
	@printf "\033[1mOrchestration & Infrastructure\033[0m\n"
	@grep -hE '^[a-zA-Z0-9_-]+:.*?## ORCH ' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## ORCH "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'
	@printf "\n\033[1mDevelopment & Running\033[0m\n"
	@grep -hE '^[a-zA-Z0-9_-]+:.*?## DEV ' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## DEV "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'
	@printf "\n\033[1mTesting & Quality\033[0m\n"
	@grep -hE '^[a-zA-Z0-9_-]+:.*?## QA ' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## QA "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'
	@printf "\n\033[1mDatabase Management\033[0m\n"
	@grep -hE '^[a-zA-Z0-9_-]+:.*?## DB ' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## DB "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'
	@printf "\n\033[1mMaintenance\033[0m\n"
	@grep -hE '^[a-zA-Z0-9_-]+:.*?## MAINT ' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## MAINT "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

# --- Orchestration & Infrastructure ---

setup: ## ORCH Install all dependencies and run initial migrations
	@echo "Installing frontend dependencies..."
	pnpm install
	@echo "Installing backend dependencies..."
	$(BACKEND_SH) uv sync
	@$(MAKE) db-migrate

redis-up: ## ORCH Start Redis container
	@if [ -n "$(CONTAINER_TOOL)" ]; then \
		engine=$$(basename "$(CONTAINER_TOOL)"); \
		if ! $$engine ps --format "{{.Names}}" | grep -q "^conceptcast-redis$$"; then \
			if $$engine ps -a --format "{{.Names}}" | grep -q "^conceptcast-redis$$"; then \
				echo "Starting existing Redis container using $$engine..."; \
				$$engine start conceptcast-redis; \
			else \
				echo "Creating and starting new Redis container using $$engine..."; \
				$$engine run -d --name conceptcast-redis -p 6379:6379 docker.io/library/redis:alpine; \
			fi; \
		else \
			echo "Redis container is already running ($$engine)."; \
		fi; \
	else \
		echo "Skipping Redis startup (no container tool found)."; \
	fi

redis-down: ## ORCH Stop Redis container
	@if [ -n "$(CONTAINER_TOOL)" ]; then \
		engine=$$(basename "$(CONTAINER_TOOL)"); \
		if $$engine ps --format "{{.Names}}" | grep -q "^conceptcast-redis$$"; then \
			echo "Stopping Redis container ($$engine)..."; \
			$$engine stop conceptcast-redis; \
		fi; \
	fi

# --- Development & Running ---

dev: redis-up ## DEV Run full stack in dev mode
	@python3 -c "import socket; s = socket.socket(); s.settimeout(0.1); s.connect(('localhost', 8000))" 2>/dev/null && (echo "Error: Port 8000 is already in use."; exit 1) || true
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
			wait "$$worker_pid" 2>/dev/null || true; \
			wait "$$backend_pid" 2>/dev/null || true; \
			cd "$$root_dir" && $(MAKE) -s redis-down; \
		}; \
		trap cleanup INT TERM EXIT; \
		setsid bash -lc "cd \"$(BACKEND_DIR)\" && uv run uvicorn main:app --app-dir src --reload --host 0.0.0.0 --port 8000" & backend_pid="$$!"; \
		$(MAKE) -s wait-for-backend; \
		$(MAKE) -s gen-api; \
		mkdir -p "$$root_dir/logs"; \
		setsid bash -lc "cd \"$(BACKEND_DIR)\" && uv run taskiq worker infra.tasks:broker --app-dir src" >"$$root_dir/logs/worker-dev.log" 2>&1 & worker_pid="$$!"; \
		set +e; \
		cd "apps/frontend" && ./node_modules/.bin/vite --host; status="$$?"; \
		set -e; \
		if [ "$$status" -eq 130 ] || [ "$$status" -eq 143 ]; then exit 0; fi; \
		exit "$$status"'

dev-backend: ## DEV Run backend application only
	$(INFISICAL) pnpm turbo run dev --filter=$(BACKEND_FILTER)

dev-frontend: ## DEV Run frontend application only
	$(INFISICAL) pnpm turbo run dev --filter=$(FRONTEND_FILTER)

dev-worker: ## DEV Run background worker only
	$(INFISICAL) pnpm turbo run worker --filter=$(BACKEND_FILTER)

gen-api: ## DEV Generate frontend API types from backend schema
	pnpm turbo run generate:api --filter=$(FRONTEND_FILTER)

wait-for-backend: 
	@echo "Waiting for backend to be ready..."
	@until curl -s "$(BASE_URL)/openapi.json" > /dev/null; do sleep 1; done
	@echo "Backend is ready."

# --- Testing, Diagnostics & Generation ---

test: test-backend ## QA Run all automated tests (backend)

test-backend: ## QA Run backend unit and integration tests (pytest). args="-k my_test"
	$(BACKEND_SH) uv run pytest $(args)

diagnose: ## QA Run agent logic diagnostics using MOCKS.
	@args="$${args:---model-id mock-analyst}"; \
	$(INFISICAL) bash -lc '$(BACKEND_SH) uv run python src/scripts/test_agents.py $$args'

generate-mock: ## QA Run E2E simulation using MOCK models for logic verification.
	@topic="$${topic:-derivatives}"; \
	$(INFISICAL) bash -lc '$(BACKEND_SH) uv run python src/scripts/e2e_cli.py --topic "$$topic"'

# --- Benchmark v2 (A/B/C arms; see benchmark-v2 repo EXPERIMENT_PLAN.md) ---

bench-council: ## BENCH Run pending Arm C (council) jobs from the v2 manifest
	@manifest="$${manifest:-../ConceptCast-benchmark-v2/manifest/jobs.csv}"; \
	$(INFISICAL) bash -lc '$(BACKEND_SH) uv run python src/scripts/benchmark_council.py --manifest "$$manifest" --arm C --parallelism $${parallelism:-4}'

bench-mono-a: ## BENCH Run pending Arm A (monolithic) jobs
	@manifest="$${manifest:-../ConceptCast-benchmark-v2/manifest/jobs.csv}"; \
	$(INFISICAL) bash -lc '$(BACKEND_SH) uv run python src/scripts/benchmark_monolithic.py --manifest "$$manifest" --arm A --parallelism $${parallelism:-4}'

bench-mono-b: ## BENCH Run pending Arm B (monolithic + repair) jobs
	@manifest="$${manifest:-../ConceptCast-benchmark-v2/manifest/jobs.csv}"; \
	$(INFISICAL) bash -lc '$(BACKEND_SH) uv run python src/scripts/benchmark_monolithic.py --manifest "$$manifest" --arm B --parallelism $${parallelism:-4}'

bench-dry: ## BENCH List pending jobs without running
	@manifest="$${manifest:-../ConceptCast-benchmark-v2/manifest/jobs.csv}"; \
	$(INFISICAL) bash -lc '$(BACKEND_SH) uv run python src/scripts/benchmark_council.py --manifest "$$manifest" --arm C --dry-run'

generate: ## QA Run ACTUAL pedagogical generation with real models. model="openai/gpt-oss-120b" topic="math"
	@topic="$${topic:-derivatives}"; \
	model="$${model:-openai/gpt-oss-120b}"; \
	$(INFISICAL) bash -lc '$(BACKEND_SH) uv run python src/scripts/e2e_cli.py --topic "$$topic" --no-mock --model-id "$$model" --analyst-model "$$model" --architect-model "$$model" --animator-model "$$model"'

lint: lint-frontend lint-backend ## QA Run all linters
lint-frontend: ## QA Run frontend linter (oxlint)
	pnpm turbo run lint --filter=$(FRONTEND_FILTER)
lint-backend: ## QA Run backend linter (ruff)
	pnpm turbo run lint --filter=$(BACKEND_FILTER)

format: format-frontend format-backend ## QA Run all formatters
format-frontend: ## QA Format frontend code (prettier)
	pnpm turbo run format --filter=$(FRONTEND_FILTER)
format-backend: ## QA Format backend code (ruff)
	$(BACKEND_SH) uv run ruff format .

typecheck: typecheck-frontend typecheck-backend ## QA Run all type checks
typecheck-frontend: ## QA Run frontend type check (tsc)
	pnpm turbo run typecheck --filter=$(FRONTEND_FILTER)
typecheck-backend: ## QA Run backend type check (mypy)
	$(BACKEND_SH) uv run mypy .

build: build-frontend build-backend ## QA Build all applications
build-frontend: ## QA Build frontend application
	pnpm turbo run build --filter=$(FRONTEND_FILTER)
build-backend: ## QA Build backend application
	pnpm turbo run build --filter=$(BACKEND_FILTER)

# --- Database Management (Backend) ---

db-migrate: ## DB Run pending database migrations
	@echo "Running backend migrations..."
	$(INFISICAL) bash -c '$(BACKEND_SH) uv run alembic upgrade head'

db-generate: ## DB Generate migration. msg="message"
	@msg="$${msg:-update}"; \
	$(INFISICAL) bash -c '$(BACKEND_SH) uv run alembic revision --autogenerate -m "$$msg"'

db-status: ## DB Show current database migration status
	$(INFISICAL) bash -c '$(BACKEND_SH) uv run alembic current'

db-rollback: ## DB Roll back the last database migration
	$(INFISICAL) bash -c '$(BACKEND_SH) uv run alembic downgrade -1'

# --- Maintenance ---

update: ## MAINT Update all dependencies to latest versions
	@echo "Updating frontend..."
	pnpm update
	@echo "Updating backend..."
	$(BACKEND_SH) uv sync --upgrade

clean: ## MAINT Remove build artifacts, node_modules, and job data
	rm -rf node_modules
	rm -rf apps/*/node_modules
	rm -rf apps/backend/.venv
	rm -rf .turbo
	rm -rf apps/frontend/dist
	rm -rf data/jobs/*
	rm -rf data/*.db*
	rm -rf reports/*
	rm -rf logs/*
	rm -f *.db*
