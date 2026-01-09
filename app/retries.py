import asyncio
import random
import time
from dataclasses import dataclass
from typing import Awaitable, Callable, Iterable, Tuple, Type


@dataclass(frozen=True)
class RetryConfig:
    max_attempts: int = 3
    base_delay_seconds: float = 0.2
    max_delay_seconds: float = 2.0
    jitter_seconds: float = 0.1


def get_retry_config() -> RetryConfig:
    from app.config import get_settings

    settings = get_settings()
    return RetryConfig(
        max_attempts=settings.retry_max_attempts,
        base_delay_seconds=settings.retry_base_delay_seconds,
        max_delay_seconds=settings.retry_max_delay_seconds,
        jitter_seconds=settings.retry_jitter_seconds,
    )


def _compute_delay(
    attempt: int,
    config: RetryConfig,
    rng: Callable[[], float],
) -> float:
    delay = min(config.max_delay_seconds, config.base_delay_seconds * (2 ** (attempt - 1)))
    if config.jitter_seconds <= 0:
        return delay
    return delay + (rng() * config.jitter_seconds)


def run_with_retries(
    func: Callable[[], object],
    *,
    exceptions: Iterable[Type[BaseException]] = (Exception,),
    config: RetryConfig | None = None,
    sleep: Callable[[float], None] = time.sleep,
    rng: Callable[[], float] = random.random,
):
    resolved_config = config or get_retry_config()
    attempts = 0

    while True:
        try:
            return func()
        except tuple(exceptions):
            attempts += 1
            if attempts >= resolved_config.max_attempts:
                raise
            delay = _compute_delay(attempts, resolved_config, rng)
            sleep(delay)


async def run_with_retries_async(
    func: Callable[[], Awaitable[object]],
    *,
    exceptions: Iterable[Type[BaseException]] = (Exception,),
    config: RetryConfig | None = None,
    sleep: Callable[[float], Awaitable[None]] = asyncio.sleep,
    rng: Callable[[], float] = random.random,
):
    resolved_config = config or get_retry_config()
    attempts = 0

    while True:
        try:
            return await func()
        except tuple(exceptions):
            attempts += 1
            if attempts >= resolved_config.max_attempts:
                raise
            delay = _compute_delay(attempts, resolved_config, rng)
            await sleep(delay)
