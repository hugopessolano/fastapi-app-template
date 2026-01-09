import unittest

from app.retries import RetryConfig, run_with_retries, run_with_retries_async


class TestRetries(unittest.TestCase):
    def test_run_with_retries_succeeds_after_failures(self) -> None:
        calls = {"count": 0}
        delays = []

        def failing_then_success():
            calls["count"] += 1
            if calls["count"] < 3:
                raise ValueError("boom")
            return "ok"

        def record_sleep(delay: float) -> None:
            delays.append(delay)

        config = RetryConfig(
            max_attempts=3,
            base_delay_seconds=1.0,
            max_delay_seconds=10.0,
            jitter_seconds=0.0,
        )

        result = run_with_retries(
            failing_then_success,
            exceptions=(ValueError,),
            config=config,
            sleep=record_sleep,
            rng=lambda: 0.0,
        )

        self.assertEqual(result, "ok")
        self.assertEqual(delays, [1.0, 2.0])

    def test_run_with_retries_raises_after_max_attempts(self) -> None:
        delays = []

        def always_fail():
            raise RuntimeError("boom")

        def record_sleep(delay: float) -> None:
            delays.append(delay)

        config = RetryConfig(
            max_attempts=2,
            base_delay_seconds=1.0,
            max_delay_seconds=10.0,
            jitter_seconds=0.0,
        )

        with self.assertRaises(RuntimeError):
            run_with_retries(
                always_fail,
                exceptions=(RuntimeError,),
                config=config,
                sleep=record_sleep,
                rng=lambda: 0.0,
            )

        self.assertEqual(delays, [1.0])


class TestRetriesAsync(unittest.IsolatedAsyncioTestCase):
    async def test_run_with_retries_async(self) -> None:
        calls = {"count": 0}
        delays = []

        async def failing_then_success():
            calls["count"] += 1
            if calls["count"] < 2:
                raise ValueError("boom")
            return "ok"

        async def record_sleep(delay: float) -> None:
            delays.append(delay)

        config = RetryConfig(
            max_attempts=2,
            base_delay_seconds=0.5,
            max_delay_seconds=10.0,
            jitter_seconds=0.0,
        )

        result = await run_with_retries_async(
            failing_then_success,
            exceptions=(ValueError,),
            config=config,
            sleep=record_sleep,
            rng=lambda: 0.0,
        )

        self.assertEqual(result, "ok")
        self.assertEqual(delays, [0.5])
