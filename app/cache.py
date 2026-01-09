import threading
import time
from dataclasses import dataclass
from typing import Awaitable, Callable

from fastapi import Request


@dataclass
class CacheEntry:
    value: object
    expires_at: float


class InMemoryCache:
    def __init__(self, time_provider: Callable[[], float] | None = None) -> None:
        self._time_provider = time_provider or time.monotonic
        self._store: dict[str, CacheEntry] = {}
        self._lock = threading.Lock()

    def get(self, key: str) -> object | None:
        now = self._time_provider()
        with self._lock:
            entry = self._store.get(key)
            if not entry:
                return None
            if entry.expires_at <= now:
                del self._store[key]
                return None
            return entry.value

    def set(self, key: str, value: object, ttl_seconds: int) -> None:
        if ttl_seconds <= 0:
            raise ValueError("ttl_seconds must be positive.")
        expires_at = self._time_provider() + ttl_seconds
        with self._lock:
            self._store[key] = CacheEntry(value=value, expires_at=expires_at)

    def delete(self, key: str) -> None:
        with self._lock:
            self._store.pop(key, None)

    def clear(self) -> None:
        with self._lock:
            self._store.clear()


_cache = InMemoryCache()


def build_cache_key(
    *,
    prefix: str,
    request: Request,
    user_id: str | None = None,
    tenant_id: str | None = None,
) -> str:
    base = f"{prefix}:{request.method}:{request.url.path}"
    query = request.url.query
    if query:
        base = f"{base}?{query}"
    if user_id:
        base = f"{base}:user={user_id}"
    if tenant_id:
        base = f"{base}:tenant={tenant_id}"
    return base


def _resolve_enabled(enabled: bool | None) -> bool:
    if enabled is None:
        from app.config import get_settings

        settings = get_settings()
        return settings.cache_enabled
    return enabled


def _resolve_ttl(ttl_seconds: int | None) -> int:
    if ttl_seconds is None:
        from app.config import get_settings

        settings = get_settings()
        return settings.cache_default_ttl_seconds
    return ttl_seconds


def cache_get(
    key: str,
    *,
    enabled: bool | None = None,
    cache: InMemoryCache | None = None,
) -> object | None:
    resolved_enabled = _resolve_enabled(enabled)
    if not resolved_enabled:
        return None
    resolved_cache = cache or _cache
    return resolved_cache.get(key)


def cache_set(
    key: str,
    value: object,
    *,
    ttl_seconds: int | None = None,
    enabled: bool | None = None,
    cache: InMemoryCache | None = None,
) -> None:
    resolved_enabled = _resolve_enabled(enabled)
    resolved_ttl = _resolve_ttl(ttl_seconds)
    if not resolved_enabled:
        return
    resolved_cache = cache or _cache
    resolved_cache.set(key, value, resolved_ttl)


def cache_delete(
    key: str,
    *,
    enabled: bool | None = None,
    cache: InMemoryCache | None = None,
) -> None:
    resolved_enabled = _resolve_enabled(enabled)
    if not resolved_enabled:
        return
    resolved_cache = cache or _cache
    resolved_cache.delete(key)


def cache_clear(
    *,
    enabled: bool | None = None,
    cache: InMemoryCache | None = None,
) -> None:
    resolved_enabled = _resolve_enabled(enabled)
    if not resolved_enabled:
        return
    resolved_cache = cache or _cache
    resolved_cache.clear()


def get_or_set(
    key: str,
    factory: Callable[[], object],
    *,
    ttl_seconds: int | None = None,
    enabled: bool | None = None,
    cache: InMemoryCache | None = None,
) -> object:
    resolved_cache = cache or _cache
    resolved_enabled = _resolve_enabled(enabled)
    resolved_ttl = _resolve_ttl(ttl_seconds)
    if not resolved_enabled:
        return factory()

    cached = resolved_cache.get(key)
    if cached is not None:
        return cached

    value = factory()
    resolved_cache.set(key, value, resolved_ttl)
    return value


async def get_or_set_async(
    key: str,
    factory: Callable[[], Awaitable[object]],
    *,
    ttl_seconds: int | None = None,
    enabled: bool | None = None,
    cache: InMemoryCache | None = None,
) -> object:
    resolved_cache = cache or _cache
    resolved_enabled = _resolve_enabled(enabled)
    resolved_ttl = _resolve_ttl(ttl_seconds)
    if not resolved_enabled:
        return await factory()

    cached = resolved_cache.get(key)
    if cached is not None:
        return cached

    value = await factory()
    resolved_cache.set(key, value, resolved_ttl)
    return value
