---
name: alembic-migrations
description: Alembic configuration and migration workflow for this repo.
metadata:
  scope: app
  auto_invoke: "Working with migrations"
---

# Alembic Migrations

## When to use
- Creating or running Alembic migrations.

## Project patterns
- `alembic.ini` sets `script_location = app/alembic` and defaults to `sqlite:///./app/app.db`.
- `app/database/alembic_utils.py` resolves the migration database URL:
  - Reads `DATABASE_URL` from `.env` if available.
  - Falls back to `app.config.get_settings().database_url`.
- Ensure `.env` is loaded before running migrations so `DATABASE_URL` is honored.
