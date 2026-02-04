# Setup Guide

Follow these instructions to get ConceptCast running locally.

## Prerequisites

- **Node.js**: >= 24 (LTS)
- **Python**: >= 3.12
- **Package Managers**: pnpm >= 9, uv

## Installation

```bash
# 1. Install JavaScript dependencies
pnpm install

# 2. Bootstrap the environment (installs Python dependencies via uv)
pnpm bootstrap
```

## Development

To start both the frontend and backend development servers simultaneously:

```bash
pnpm dev
```

- **Frontend**: http://localhost:5173
- **Backend**: http://localhost:8000

## Testing

Run unit and integration tests for both services:

```bash
pnpm test
```
