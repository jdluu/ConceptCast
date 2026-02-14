# Stage 1: build frontend (same-origin API in production)
FROM node:20-alpine AS frontend-build
RUN corepack enable && corepack prepare pnpm@latest --activate
WORKDIR /app
COPY apps/frontend/package.json ./
RUN pnpm install --frozen-lockfile 2>/dev/null || pnpm install
COPY apps/frontend ./
ENV VITE_API_url=
RUN pnpm run build

# Stage 2: backend + frontend dist
FROM python:3.11-slim
RUN pip install uv
WORKDIR /app
COPY apps/backend/pyproject.toml apps/backend/uv.lock* ./
RUN uv sync --frozen --no-dev --no-install-project 2>/dev/null || true
COPY apps/backend/src ./src
RUN uv sync --frozen --no-dev
COPY --from=frontend-build /app/dist ./frontend_dist
ENV PYTHONPATH=/app/src
ENV FRONTEND_DIST=/app/frontend_dist
EXPOSE 8000
CMD ["uv", "run", "uvicorn", "main:app", "--app-dir", "src", "--host", "0.0.0.0", "--port", "8000"]
