.PHONY: setup update dev dev-backend dev-frontend db-migrate clean

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
dev:
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
