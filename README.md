# ConceptCast

## Overview

ConceptCast uses AI to turn complex ideas into clear educational videos. It employs a team of specialized agents to research, storyboard, and script animations using the Manim engine.

The goal is to support critical thinking rather than replace it. ConceptCast automates the difficult parts of coding visualizations, making it easier to produce quality tutorials for math, science, and business.

## Tech Stack

### Frontend
- **React + Vite**: High-performance, reactive user dashboard.
- **TanStack Query**: Asynchronous state management.
- **Zustand**: Client-side global state management.
- **React Router**: Client-side routing.
- **Tailwind CSS v4**: Utility-first styling with Vite integration.
- **TypeScript**: Type-safety across the monorepo.
- **Oxlint & Vitest**: Fast linting and unit testing.

### Backend
- **FastAPI (Python)**: Async web framework for orchestrating agents.
- **uv**: High-speed Python package and project manager.
- **Manim Community**: Mathematical animation engine.
- **Pydantic**: Data validation and settings management.
- **Loguru**: Enhanced logging.
- **Ruff & Pytest**: Linting and testing.

### Monorepo
- **Turborepo**: High-performance build system.
- **pnpm**: Fast, disk-efficient package manager.
- **GitHub Actions**: CI/CD for testing and documentation.

## Getting Started

### Prerequisites

- Node.js >= 22 (LTS)
- Python >= 3.11
- pnpm >= 9
- uv

### Installation

```bash
# 1. Install JavaScript dependencies
pnpm install

# 2. Bootstrap the environment (installs Python dependencies via uv)
pnpm bootstrap
```

### Development

```bash
# Start both frontend and backend development servers
pnpm dev
```

### Testing

```bash
# Run unit tests for both frontend and backend
pnpm test
```
