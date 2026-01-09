import unittest

from app.cache import InMemoryCache, get_or_set


class FakeClock:
    def __init__(self) -> None:
        self._now = 0.0

    def advance(self, seconds: float) -> None:
        self._now += seconds

    def __call__(self) -> float:
        return self._now


class TestCache(unittest.TestCase):
    def test_cache_expires_entries(self) -> None:
        clock = FakeClock()
        cache = InMemoryCache(time_provider=clock)

        cache.set("key", "value", ttl_seconds=5)
        self.assertEqual(cache.get("key"), "value")

        clock.advance(6)
        self.assertIsNone(cache.get("key"))

    def test_get_or_set_uses_cached_value(self) -> None:
        clock = FakeClock()
        cache = InMemoryCache(time_provider=clock)
        calls = {"count": 0}

        def factory():
            calls["count"] += 1
            return f"value-{calls['count']}"

        first = get_or_set(
            "key",
            factory,
            ttl_seconds=10,
            enabled=True,
            cache=cache,
        )
        second = get_or_set(
            "key",
            factory,
            ttl_seconds=10,
            enabled=True,
            cache=cache,
        )

        self.assertEqual(first, "value-1")
        self.assertEqual(second, "value-1")
        self.assertEqual(calls["count"], 1)
