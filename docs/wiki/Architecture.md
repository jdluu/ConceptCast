# Architecture

ConceptCast is a modular system designed for automated educational video production.

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

## AI Agents (The Council)

ConceptCast uses a "Council" of specialized agents to automate the video creation process.

### Analyst Agent ("The Pedagogue")
- **Responsibility**: Deconstructs a complex topic into a sequential series of pedagogical steps (`TeachingStep`).
- **Philosophy**: Employs "The Whiteboard Standard" - clear, sequential logic focusing on derivations rather than just answers.
- **Model**: `google-gla:gemini-1.5-pro` via `pydantic-ai`.
- **Output**: Generates a `CurriculumPlan`.
