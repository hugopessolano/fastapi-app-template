# Soft Delete Guide

This guide explains how soft delete works in the template and how to use it correctly.

## 1) What soft delete means
Soft delete keeps records in the database but marks them as deleted using a timestamp:
- `deleted_at = NULL` means the record is active.
- `deleted_at = <timestamp>` means the record is deleted.

This preserves history and prevents accidental data loss.

## 2) Default query behavior
All normal queries automatically exclude soft-deleted records.
This happens because a global SQLAlchemy filter is applied at session level.

If you need to include deleted rows explicitly, use:
```
from app.database.soft_delete import query_with_deleted

query_with_deleted(db, ModelName).all()
```

## 3) Cascade behavior (opt-in)
Soft delete cascades only through relationships marked with:
```
info={"soft_delete_cascade": True}
```

This is intentional so each model controls which dependencies are deleted.

Example:
```
roles: Mapped[List["RolePermissions"]] = relationship(
    "RolePermissions",
    back_populates="role",
    info={"soft_delete_cascade": True},
)
```

## 4) Operation lifecycle
1. The API receives a DELETE request.
2. The endpoint calls `soft_delete_by_id(db, Model, id)`.
3. The target record gets `deleted_at` set to the current UTC timestamp.
4. Relationships marked for cascade are recursively soft-deleted.
5. The transaction commits.

If the record does not exist or is already deleted, the operation returns `False`.

## 5) Adding a new model
When you create a new model:
1. Inherit from `Base` so it gets `deleted_at`.
2. Decide which relationships should be soft-deleted and mark them with `info`.
3. If you need to list deleted records, use `query_with_deleted`.

## 6) Notes and pitfalls
- SQL views or raw SQL must filter `deleted_at` manually.
- Keep cascade paths small and intentional to avoid large deletes.
- Cycles are prevented internally, but avoid broad cascade graphs.
