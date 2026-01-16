---
name: fastapi-core
description: FastAPI router patterns and app wiring used in this project.
metadata:
  scope: app
  auto_invoke: "Adding or updating FastAPI endpoints"
---

# FastAPI Core

## When to use
- Creating or modifying API routers and dependencies.
- Wiring new routes into the application.

## Project patterns
- Routers live in `app/routers/v1/` and use `API_PREFIX` from `app/routers/v1/__init__.py`.
- Keep routers thin. Delegate business logic to `app/endpoints_logic/v1/<resource>.py`.
- Dependency pattern:
  - `db: Session = Depends(get_db)`
  - `auth: AuthContext = Depends(get_auth_context)` for protected routes.
  - `tenant_ctx: TenantContext = Depends(get_tenant_context)` for tenant-scoped routes.
- Pagination and ordering parameters use `Query` defaults and are passed to logic helpers.
- Router inclusion is driven by `app/routers/registry.py` and `app/routers/registry_data.json`.
  - `requires_auth` entries are skipped when `AUTH_MODE=disabled`.
