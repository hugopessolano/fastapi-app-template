# Cache Guide

This guide explains the caching helpers included in the template.

## 1) What the cache does
The cache stores computed values in memory for a short time to avoid repeating expensive work.
It is opt-in per endpoint and disabled by default.

## 2) Enabling the cache
Set in `.env`:
```
CACHE_ENABLED=true
CACHE_DEFAULT_TTL_SECONDS=60
```

## 3) Basic usage (sync)
```
from app.cache import build_cache_key, get_or_set

@router.get("/stats")
async def get_stats(request: Request):
    key = build_cache_key(prefix="stats", request=request)
    return get_or_set(key, compute_stats, ttl_seconds=120)
```

## 4) Basic usage (async)
```
from app.cache import build_cache_key, get_or_set_async

@router.get("/reports")
async def get_reports(request: Request):
    key = build_cache_key(prefix="reports", request=request)
    return await get_or_set_async(key, fetch_reports, ttl_seconds=60)
```

## 5) Varying by user or tenant
Use `user_id` or `tenant_id` in the cache key:
```
key = build_cache_key(
    prefix="reports",
    request=request,
    user_id=str(auth.user.id),
    tenant_id="tenant-123",
)
```

## 6) Invalidation
If you update or delete data, clear the relevant cache keys:
```
from app.cache import cache_delete
```

For a full reset:
```
from app.cache import cache_clear
```
Both helpers are no-ops when `CACHE_ENABLED=false`.

## 7) Notes and limits
- The cache is in-memory and process-local.
- Each worker has its own cache.
- Use short TTLs and avoid caching sensitive data.
