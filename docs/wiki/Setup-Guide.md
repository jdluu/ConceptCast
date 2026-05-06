# Setup Guide

## Prerequisites
- Node.js >= 22
- Python >= 3.11
- Podman (recommended for sandboxing Manim rendering)
- Manim (locally if fallback execution is needed)

## Configuration

### Infisical Authentication
This project uses Infisical for secret management. You must authenticate before starting development:
```bash
infisical login
```

### Recommended Setup (from Root)
```bash
make setup
```

### Manual Installation (Fallback)
```bash
pnpm install
cd apps/backend && uv sync
```

## Running the Application
From the root directory:
```bash
make dev
```
This will start Redis, the backend (port 8000), the background worker, and the frontend (port 5173). Secrets are automatically injected via Infisical.
