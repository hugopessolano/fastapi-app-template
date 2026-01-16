---
name: sqlalchemy-models
description: SQLAlchemy model conventions for this template.
metadata:
  scope: app
  auto_invoke: "Adding or modifying database models"
---

# SQLAlchemy Models

## When to use
- Creating or editing models under `app/database/models/`.

## Project patterns
- Base class is `Base` in `app/database/models/base_models.py` and includes:
  - `TimestampMixin` (`created_at`, `updated_at`).
  - `SoftDeleteMixin` (`deleted_at`).
- Use `Mapped` + `mapped_column` for typed columns when possible.
- Define `__tablename__` explicitly.
- Relationships often include `info={"soft_delete_cascade": True}` for soft delete cascades.
- UUID primary keys are commonly used for core entities.
