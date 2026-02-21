# Architecture

ConceptCast is a monorepo consisting of a FastAPI backend and a Vite/React frontend.

## Data Flow

```mermaid
graph TD
    User((User)) -- "Topic + Audience" --> Frontend[Vite/React/Tailwind 4]
    Frontend -- "Job Request (POST /jobs)" --> Backend[FastAPI]
    Backend -- "SQLAlchemy" --> DB[(SQLite/JobRecord)]
    
    subgraph "Orchestration Council"
        Backend -- "Task" --> Orchestrator[Workflow Orchestrator]
        Orchestrator -- "Step 1" --> Planner[Planning Agent]
        Orchestrator -- "Step 2" --> Validator[Validation Agent (Stub)]
        Orchestrator -- "Step 3" --> Architect[Architect Agent]
        Orchestrator -- "Step 4" --> Animator[Animator Agent]
    end
    
    Animator -- "Manim Script" --> Renderer[Rendering Service]
    Renderer -- "Podman Sandbox" --> Manim[Manim Engine]
    Manim -- "MP4 Artifact" --> Storage[Local Storage /data/jobs]
    
    Backend -- "SSE Events" --> Frontend
    Storage -- "Static Serve" --> Frontend
```

## Key Technologies
- **Backend**: FastAPI, Pydantic AI, SQLAlchemy (Async), Manim Engine.
- **Frontend**: React 19, Vite, Tailwind CSS 4, Framer Motion.
- **Infrastructure**: Podman for sandboxed rendering (with local execution fallback).
