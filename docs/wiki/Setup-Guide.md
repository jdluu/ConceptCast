# Setup Guide

## Prerequisites
- Node.js >= 24
- Python >= 3.11
- Docker (for Manim rendering)
- Manim (locally if not using Docker)

## Installation

### Root Dependencies
```bash
pnpm install
```

### Backend Setup
```bash
cd apps/backend
uv venv
source .venv/bin/activate
uv sync
```

### Frontend Setup
```bash
cd apps/frontend
pnpm install
```

## Running the Application
From the root directory:
```bash
pnpm dev
```
This will start both the backend (port 8000) and frontend (host/vite).
