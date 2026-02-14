FROM python:3.11-slim

RUN pip install uv

WORKDIR /app

# Copy dependency definition files from apps/backend to root of container app
COPY apps/backend/pyproject.toml apps/backend/uv.lock* ./

# Install dependencies
RUN uv sync --frozen --no-dev --no-install-project 2>/dev/null || true

# Copy source code
COPY apps/backend/src ./src

# Install project
RUN uv sync --frozen --no-dev

ENV PYTHONPATH=/app/src
EXPOSE 8000

CMD ["uv", "run", "uvicorn", "main:app", "--app-dir", "src", "--host", "0.0.0.0", "--port", "8000"]
