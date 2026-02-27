.PHONY: setup update dev dev-backend dev-frontend db-migrate clean redis-up redis-down

# Start Redis container using Podman
redis-up:
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

# Stop Redis container
redis-down:
	@if podman ps --format "{{.Names}}" | grep -q "^conceptcast-redis$$"; then \
		echo "Stopping Redis container..."; \
		podman stop conceptcast-redis; \
	fi

# Setup project dependencies
setup:
	@echo "Installing frontend dependencies..."
	pnpm install
	@echo "Installing backend dependencies..."
	cd apps/backend && uv sync
	@make db-migrate

# Update all dependencies
update:
	@echo "Updating frontend..."
	pnpm update
	@echo "Updating backend..."
	cd apps/backend && uv sync --upgrade

# Run full stack in dev mode
dev: redis-up
	pnpm turbo run dev worker

# Run backend only
dev-backend:
	pnpm turbo run dev --filter=backend

# Run frontend only
dev-frontend:
	pnpm turbo run dev --filter=concept-cast-frontend

# Run background worker only
dev-worker:
	pnpm turbo run worker --filter=backend

worker: dev-worker

# Run database migrations (Backend)
db-migrate:
	@echo "Running backend migrations..."
	cd apps/backend && uv run alembic upgrade head

# Generate API types (Frontend)
gen-api:
	pnpm turbo run generate:api --filter=concept-cast-frontend

# Clean build artifacts
clean:
	rm -rf node_modules
	rm -rf apps/*/node_modules
	rm -rf apps/backend/.venv
	rm -rf .turbo
