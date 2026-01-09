# Auth and Tenant Context Guide

This guide explains how authentication and tenant scoping are separated in the template.

## 1) Overview
- `AuthContext` handles authentication and authorization state.
- `TenantContext` handles tenant scoping and can be disabled independently.

This separation lets you keep auth while turning off tenant routing, or keep tenants enabled without coupling to auth internals.

## 2) AuthContext modes
`AuthContext` is produced by `get_auth_context()` and only concerns auth:
- `built_in`: validates JWT and loads the current user.
- `disabled`: returns a permissive context (no user, no auth checks).
- `custom`: raises 501 until you provide your own dependency.

`AuthContext` does not store tenant assignments anymore.

## 3) TenantContext behavior
`TenantContext` is produced by `get_tenant_context()` and depends on:
- `TENANTS_ENABLED`: when `false`, tenant scoping is disabled.
- `AUTH_MODE`: when `disabled`, tenant scoping is permissive.

When scoping is active, the context exposes `allowed_tenant_ids` from the current user.

## 4) Request lifecycle (high level)
1. The router injects `AuthContext` and `TenantContext`.
2. `AuthContext` validates auth based on `AUTH_MODE`.
3. `TenantContext` decides whether scoping is enabled.
4. Endpoints use `TenantContext` to filter queries when needed.

## 5) Using contexts in routers
Example for tenant-scoped routes:
```
from fastapi import Depends
from app.auth.context import AuthContext, get_auth_context
from app.tenants.context import TenantContext, get_tenant_context
from app.routers.utils import filter_by_tenant

@router.get("/items")
async def list_items(
    auth: AuthContext = Depends(get_auth_context),
    tenant_ctx: TenantContext = Depends(get_tenant_context),
):
    query = db.query(Item)
    if tenant_ctx.enabled and not tenant_ctx.cross_tenant_allowed:
        query = filter_by_tenant(query, Item, tenant_ctx.allowed_tenant_ids)
    return query.all()
```

If a route does not need tenant scoping, inject only `AuthContext`.

## 6) Adding new routers
1. Always inject `AuthContext` so `AUTH_MODE` is respected.
2. Inject `TenantContext` only if the resource is tenant-scoped.
3. Use `filter_by_tenant()` for consistent filtering behavior.

## 7) Notes and pitfalls
- If `TENANTS_ENABLED=false`, do not access `user.tenants` directly.
- In `AUTH_MODE=custom`, return an `AuthContext`-compatible object.
- Keep tenant scoping logic inside `TenantContext` to avoid coupling.
