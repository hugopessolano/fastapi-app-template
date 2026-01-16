---
name: external-db-connections
description: External DB registry and permissioned connection helpers.
metadata:
  scope: app
  auto_invoke: "Adding external DB integrations"
---

# External DB Connections

## When to use
- Wiring new external databases or permissions.

## Project patterns
- `app/database/external_registry.py` reads:
  - `EXTERNAL_DB_<NAME>_URL`
  - `EXTERNAL_DB_<NAME>_PERMISSIONS`
  - Legacy `EXTERNAL_DB_URL` and `EXTERNAL_DB_PERMISSIONS`.
- Permissions default to all when not set and are validated against `create/read/update/delete`.
- `external_db_dependency(name, permissions)` yields a SQLAlchemy session for FastAPI routes.
- `docs/external-db-guide.md` documents setup and examples.
