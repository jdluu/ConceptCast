# ConceptCast

ConceptCast turns complex ideas into clear educational videos using AI. An
**Agent Council** of specialized agents (Analyst → Architect → Animator)
shares state through a **Global Context Object (GCO)** to research, storyboard,
and render animations with the [Manim](https://www.manim.community/) engine,
protected by an AST-driven validation and diff-repair loop.

This repository contains the application source code. The ConceptCast project
spans two companion repositories:

| Repository | Contents |
|---|---|
| **[ConceptCast](https://github.com/jdluu/ConceptCast)** (this repo) | Application source code |
| **[ConceptCast-results](https://github.com/jdluu/ConceptCast-results)** | Benchmark data, raw execution logs, figures, SQLite snapshot, reproducibility verifiers |

## Repository Layout

| Path | Purpose |
|---|---|
| `apps/backend` | FastAPI service + Pydantic AI agent council |
| `apps/frontend` | Web UI |
| `prompts/` | Agent prompts and vendored ManimCE skill docs |
| `scripts/` | DB snapshotting, wait helpers, Infisical token |
| `docs/wiki/` | Architecture deep dive and setup guide |
| `run_topic.sh` / `run_all_*.sh` | Benchmark runners (one topic × 9 models) |

## Quick Start

### Prerequisites

- Node.js ≥ 22 ([nvm](https://github.com/nvm-sh/nvm) recommended; see `.nvmrc`)
- [pnpm](https://pnpm.io/) ≥ 9 (`corepack enable` works too)
- Python ≥ 3.11 with [uv](https://docs.astral.sh/uv/)
- Redis (the Makefile starts one via container runtime)
- Podman *or* Docker (sandboxed Manim rendering)
- A Manim installation locally if you want non-sandboxed rendering fallback

### 1. Clone

```bash
git clone https://github.com/jdluu/ConceptCast.git
cd ConceptCast

# Recommended: benchmark data + verifiers (sibling repo, cloned into results/)
git clone https://github.com/jdluu/ConceptCast-results.git results
```

> The `results/` path is gitignored here, so cloning the sibling
> ConceptCast-results repository inside the code repo is safe and keeps every
> relative path in the scripts working.

### 2. Configure secrets

Secrets are managed with [Infisical](https://infisical.com/) (project folder
`/ConceptCast/ai`). Either:

```bash
infisical login          # then run everything through: infisical run -- make dev
```

or skip Infisical entirely by copying the template and filling in local keys:

```bash
cp env.example .env      # set NANO_API_KEY and CONTEXT7_API_KEY
```

`.env` is gitignored — never commit real keys.

### 3. Install and run

```bash
make setup     # installs pnpm deps, backend venv, runs migrations
make dev       # redis + backend :8000 + worker + frontend :5173
```

Then open http://localhost:5173.

## Generating Animations

Single generation with a real model:

```bash
make generate model="openai/gpt-oss-120b" topic="the Fourier transform"
```

Logic-only smoke test without API calls:

```bash
make diagnose       # agent logic diagnostics with mocks
make generate-mock  # full E2E simulation with mock models
```

Full benchmark sweep (all nine models on one topic, bounded parallelism):

```bash
./run_topic.sh "eigenvectors"
PARALLELISM=4 ./run_topic.sh "backpropagation" "General Audience"
```

Runner outputs land in `results/reports/<topic>/` and
`results/data/conceptcast.db` when the companion repository is cloned into
`results/`; otherwise they stay under the gitignored `reports/` and `data/`.

## Development

```bash
make test        # pytest suite
make lint        # oxlint + ruff
make typecheck   # tsc + mypy
make format      # prettier + ruff format
make db-migrate  # apply pending migrations
```

See [`docs/wiki/Setup-Guide.md`](docs/wiki/Setup-Guide.md) for manual
installation details and [`docs/wiki/Architecture.md`](docs/wiki/Architecture.md)
for how the council, GCO, and repair loop fit together.

## License & Attribution

Released for academic reproducibility and public research verification.
Licensed under the MIT License (see [LICENSE](LICENSE)). Benchmark data and
verifiers in the results repository are likewise MIT-licensed.
