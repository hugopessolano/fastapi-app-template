import math
import threading
import time
from collections import deque
from typing import Callable, Deque, Dict, Tuple

from fastapi import Depends, HTTPException, Request

from app.auth.context import AuthContext, get_auth_context


class InMemoryRateLimiter:
    def __init__(self, time_provider: Callable[[], float] | None = None) -> None:
        self._time_provider = time_provider or time.monotonic
        self._buckets: Dict[str, Deque[float]] = {}
        self._lock = threading.Lock()

    def allow(self, key: str, max_requests: int, window_seconds: int) -> Tuple[bool, int | None]:
        now = self._time_provider()
        window_start = now - window_seconds

        with self._lock:
            bucket = self._buckets.setdefault(key, deque())
            while bucket and bucket[0] <= window_start:
                bucket.popleft()

            if len(bucket) >= max_requests:
                retry_after = math.ceil(window_seconds - (now - bucket[0]))
                return False, max(0, retry_after)

            bucket.append(now)
            return True, None


_rate_limiter = InMemoryRateLimiter()


def _resolve_limits(max_requests: int | None, window_seconds: int | None) -> Tuple[int, int]:
    from app.config import get_settings

    settings = get_settings()
    resolved_max = max_requests or settings.rate_limit_default_requests
    resolved_window = window_seconds or settings.rate_limit_default_window_seconds

    if resolved_max <= 0 or resolved_window <= 0:
        raise ValueError("Rate limit values must be positive.")

    return resolved_max, resolved_window


def _enforce_rate_limit(
    key: str,
    max_requests: int | None,
    window_seconds: int | None,
) -> None:
    resolved_max, resolved_window = _resolve_limits(max_requests, window_seconds)
    allowed, retry_after = _rate_limiter.allow(key, resolved_max, resolved_window)
    if allowed:
        return

    raise HTTPException(
        status_code=429,
        detail="Rate limit exceeded",
        headers={"Retry-After": str(retry_after or 0)},
    )


def rate_limit_by_ip(
    *,
    max_requests: int | None = None,
    window_seconds: int | None = None,
):
    async def dependency(request: Request) -> None:
        client = request.client.host if request.client else "unknown"
        _enforce_rate_limit(client, max_requests, window_seconds)

    return dependency


def rate_limit_by_user(
    *,
    max_requests: int | None = None,
    window_seconds: int | None = None,
):
    async def dependency(
        request: Request,
        auth: AuthContext = Depends(get_auth_context),
    ) -> None:
        user_id = getattr(auth.user, "id", None)
        key = user_id or (request.client.host if request.client else "unknown")
        _enforce_rate_limit(key, max_requests, window_seconds)

    return dependency
