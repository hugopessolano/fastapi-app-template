import unittest

from app.rate_limit import InMemoryRateLimiter


class FakeClock:
    def __init__(self) -> None:
        self._now = 0.0

    def advance(self, seconds: float) -> None:
        self._now += seconds

    def __call__(self) -> float:
        return self._now


class TestRateLimiter(unittest.TestCase):
    def test_allows_requests_within_window(self) -> None:
        clock = FakeClock()
        limiter = InMemoryRateLimiter(time_provider=clock)

        allowed, retry_after = limiter.allow("user-1", max_requests=2, window_seconds=10)
        self.assertTrue(allowed)
        self.assertIsNone(retry_after)

        clock.advance(1)
        allowed, retry_after = limiter.allow("user-1", max_requests=2, window_seconds=10)
        self.assertTrue(allowed)
        self.assertIsNone(retry_after)

        clock.advance(1)
        allowed, retry_after = limiter.allow("user-1", max_requests=2, window_seconds=10)
        self.assertFalse(allowed)
        self.assertEqual(retry_after, 8)

        clock.advance(9)
        allowed, retry_after = limiter.allow("user-1", max_requests=2, window_seconds=10)
        self.assertTrue(allowed)
        self.assertIsNone(retry_after)

    def test_rate_limits_are_isolated_per_key(self) -> None:
        clock = FakeClock()
        limiter = InMemoryRateLimiter(time_provider=clock)

        limiter.allow("user-1", max_requests=1, window_seconds=10)
        allowed, _ = limiter.allow("user-2", max_requests=1, window_seconds=10)

        self.assertTrue(allowed)
