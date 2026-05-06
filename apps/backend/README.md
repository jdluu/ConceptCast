# ConceptCast Backend

FastAPI service and AI Agent Council for the ConceptCast application.

## Features
- FastAPI
- Pydantic AI (Agent Orchestration)
- SQLAlchemy (Async)
- Taskiq (Background Jobs)

## Development

Run the development server:
```bash
uv run uvicorn main:app --app-dir src --reload
```

Run background worker:
```bash
uv run taskiq worker infra.tasks:broker --app-dir src
```

## Database

Generate migration:
```bash
uv run alembic revision --autogenerate -m "message"
```

Apply migrations:
```bash
uv run alembic upgrade head
```
