---
name: docker-workflow
description: Docker Compose layout for API, scaffold API, and scaffold UI.
metadata:
  scope: root
  auto_invoke: "Changing docker or runtime configuration"
---

# Docker Workflow

## When to use
- Modifying Docker services or local runtime setup.

## Project patterns
- Root `docker-compose.yml` defines the `api` service only (FastAPI, port 8000, `.env` injected).
- Scaffold tooling runs via `tools/scaffold/docker-compose.yml` with:
  - `scaffold-api` (port 8001, `SCAFFOLD_TEMPLATE_ROOT` env).
  - `scaffold-ui` (port 3000, `NEXT_PUBLIC_SCAFFOLD_API_URL` env).
- Source is mounted into containers for live reload.
- Root `Dockerfile` builds the FastAPI image with `python:3.13-slim` and runs `uvicorn`.
