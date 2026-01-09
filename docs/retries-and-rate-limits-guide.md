# Retries and Rate Limiting Guide

This guide explains how retries and rate limiting work in the template.

## 1) Retries (progressive backoff)
Use `run_with_retries` or `run_with_retries_async` when calling external services.

Example (sync):
```
from app.retries import run_with_retries

def fetch_remote():
    return client.get("https://example.com").json()

data = run_with_retries(fetch_remote)
```

Example (async):
```
from app.retries import run_with_retries_async

async def fetch_remote():
    return await client.get("https://example.com")

data = await run_with_retries_async(fetch_remote)
```

Defaults come from `.env`:
- `RETRY_MAX_ATTEMPTS`
- `RETRY_BASE_DELAY_SECONDS`
- `RETRY_MAX_DELAY_SECONDS`
- `RETRY_JITTER_SECONDS`

You can override defaults by passing a `RetryConfig`.

## 2) Rate limiting (opt-in)
Rate limiting is opt-in per endpoint. Add one of the dependencies:

IP-based:
```
from fastapi import Depends
from app.rate_limit import rate_limit_by_ip

@router.get("/public", dependencies=[Depends(rate_limit_by_ip())])
async def public_endpoint():
    return {"ok": True}
```

User-based (falls back to IP if no user is present):
```
from fastapi import Depends
from app.rate_limit import rate_limit_by_user

@router.get("/secure", dependencies=[Depends(rate_limit_by_user())])
async def secure_endpoint():
    return {"ok": True}
```

Defaults come from `.env`:
- `RATE_LIMIT_DEFAULT_REQUESTS`
- `RATE_LIMIT_DEFAULT_WINDOW_SECONDS`

You can override per endpoint:
```
Depends(rate_limit_by_ip(max_requests=20, window_seconds=60))
```

## 3) Notes
- The limiter is in-memory and process-local.
- Use IP-based limits for public routes.
- Use user-based limits for authenticated routes.
