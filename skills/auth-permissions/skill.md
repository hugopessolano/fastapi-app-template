---
name: auth-permissions
description: AuthContext behavior and permission auto-build rules.
metadata:
  scope: app
  auto_invoke: "Auth mode or permissions changes"
---

# Auth and Permissions

## When to use
- Changing authentication behavior or permission rules.

## Project patterns
- `app/auth/context.py` returns an `AuthContext` that depends on `AUTH_MODE`:
  - `disabled`: permissive context, no user, no token required.
  - `custom`: raises 501 until a custom dependency is provided.
  - `built_in`: requires token and resolves the current user.
- `app/auth/build_permissions.py` builds permissions from router tags, methods, and route names.
  - Restores soft-deleted permissions when they reappear.
  - Uses the `Permissions` model and commits updates.
