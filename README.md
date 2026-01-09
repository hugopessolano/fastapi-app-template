# FastAPI Backend Template

This template provides a didactic starting point for FastAPI projects. It ships with:
- Example routers (`tenants`, `users`) to demonstrate CRUD patterns (pagination, ordering, tenant scoping, role/tenant assignments).
- Authentication and authorization (JWT + permissions derived from routes).
- Structured logging (stdout + SQLite) and a sample SQL view for reporting.
- Seed helpers to create a default admin user and a base tenant.
- Optional connector to secondary databases via `EXTERNAL_DB_URL`.
- Soft delete support with `deleted_at` and automatic query filtering.
- Docker workflow plus documentation to guide developers with little experience.

## Key Features
- FastAPI + SQLAlchemy 2.0 + Alembic already wired.
- Central configuration via `app/config.py` powered by `pydantic-settings`.
- Switchable auth modes: `built_in`, `disabled`, `custom` (set in `.env`).
- Logging to console and SQLite (`LOGS_DB_PATH`), with routers emitting logs out of the box.
- Docs directory (`docs/`) with quickstart, how-to-test, and customization checklist.

## Repository Layout

| Path | Description |
| --- | --- |
| `app/` | Application code (routers, auth, models, middleware, views). |
| `app/config.py` | Single source of configuration. |
| `docs/` | Didactic guides (quickstart, how_to_test, customization-checklist). |
| `docker-compose.yml` / `Dockerfile` | Docker workflow for local dev/testing. |

## Authentication Modes
Set `AUTH_MODE` inside `.env` (default `built_in`):

| Mode | Behavior |
| --- | --- |
| `built_in` | OAuth2 password flow + JWT (`/v1/auth/login`). Routers depend on `AuthContext`. |
| `disabled` | Auth is bypassed; `AuthContext` becomes permissive (ideal for prototyping). |
| `custom` | Placeholder to plug your own provider; the template raises 501 until you supply it. |

Seeds (when enabled) create `admin@admin.com` / `admin` linked to the base tenant.
`TENANTS_ENABLED` controls whether `/v1/tenants` is exposed (defaults to `true`).

## Getting Started
1. Copy the environment file.
   ```bash
   cp .env.example .env
   ```
2. Choose how to run:

   **Option A - Local Python**
   ```bash
   pip install -r requirements.txt
   uvicorn app.main:app --reload --port 8000
   ```

   **Option B - Docker Compose (recommended)**
   ```bash
   docker compose up --build
   ```
   - API: `http://localhost:8000/`
   - Docs: `http://localhost:8000/docs`
   - Stop with `Ctrl+C` or `docker compose down`.

On startup the app:
1. Creates tables (Alembic metadata).
2. Optionally builds permissions (`AUTO_BUILD_PERMISSIONS=true`).
3. Optionally seeds admin/tenant (`ENABLE_SEED_DATA=true`).

## How to Extend the Template
1. **Models**: add SQLAlchemy models in `app/database/models/` and generate migrations with Alembic.
2. **Schemas**: create Pydantic models in `app/schemas/`.
3. **Router**: follow `app/routers/v1/tenants.py` for CRUD, pagination, and tenant filtering.
4. **Register**: include the router in `app/main.py` and set tags (permissions use them).
5. **Document**: describe extra setup (seeds, config flags) inside `docs/`.

Tips:
- Inject `AuthContext` into new routers so they respect `AUTH_MODE`.
- Reuse helpers (`filter_by_tenant`, `calculate_next_and_last_pages`, `order_by_parameter`).
- Update `app/initialization.py` only if new features need seed data (guard them with config flags).

## Extending Configuration
1. Add a new attribute to `Settings` in `app/config.py` with a sensible default.
2. Expose it in `.env.example`.
3. Import `get_settings()` where needed to read the value.
4. Update docs so teammates know how to set it.

## Logging & Monitoring
- `logging_stdout_level` and `logging_db_level` (from `.env`) control console/SQLite logging.
- `LOGS_DB_PATH` may point outside `app/`; the template creates directories automatically.
- Inspect logs quickly with `sqlite3 path/to/logs.db "SELECT * FROM logs ORDER BY id DESC LIMIT 20;"`.
- Routers (`tenants`, `users`, `roles`, `permissions`, `auth`) log actions (list/create/update/delete). Use them as examples when instrumenting new routers.
- `app/views/view_queries.py` defines `tenants_user_counts` to illustrate reporting with SQL views.

## External Data Sources
- Set `EXTERNAL_DB_URL` in `.env` when you need to talk to another database (e.g., legacy MariaDB, reporting warehouse).
- Use the helper dependency provided in `app/database/external.py`:
  ```python
  from fastapi import Depends
  from app.database.external import get_external_db

  @router.get("/external-stats")
  async def read_external_stats(conn = Depends(get_external_db)):
      result = conn.execute("SELECT COUNT(*) FROM legacy_table").scalar()
      return {"legacy_count": result}
  ```
- If `EXTERNAL_DB_URL` is empty, `get_external_db()` raises a clear error so you can guard routes or fallback gracefully.

## Additional Resources
- `docs/quickstart.md`: run the template (Docker-first) and hit your first endpoint.
- `docs/how_to_test.md`: testing script covering auth toggle, logs, and `/v1/users`.
- `docs/customization-checklist.md`: checklist for adapting the template (naming, config, auth, docs).
- `docs/external-db-guide.md`: paso a paso para conectar bases externas usando `EXTERNAL_DB_URL`.
- `docs/alembic-guide.md`: guide to create and apply migrations safely.
- `docs/soft-delete-guide.md`: soft delete behavior and how to use cascades.
- `docs/auth-and-tenant-context-guide.md`: how auth and tenant scoping are separated.

Use the issues tracker or your team's knowledge base to capture improvement ideas as you work with the template.
