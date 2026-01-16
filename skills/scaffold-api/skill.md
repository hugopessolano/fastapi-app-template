---
name: scaffold-api
description: Scaffold API endpoints for specs, settings, and external DBs.
metadata:
  scope: tools/scaffold/api
  auto_invoke: "Changing scaffold API endpoints"
---

# Scaffold API

## When to use
- Updating the scaffold API or its request/response contracts.

## Project patterns
- `tools/scaffold/api/app.py` exposes endpoints for:
  - Specs: `/specs`, `/specs/read`, `/specs/write`.
  - Scaffolding: `/scaffold/create`, `/scaffold/modify`, `/scaffold/sync*`, `/scaffold/remove`.
  - Settings: `/settings` read/write to `.env`.
  - External DBs: `/external-dbs`, `/external-dbs/delete`, `/external-dbs/test`.
- Spec writes call `tools/scaffold/spec.validate_spec`.
- External DB validation uses SQLAlchemy URL parsing and returns clear 400 errors.
- Registry updates are handled by `tools/scaffold/registry.py`.
