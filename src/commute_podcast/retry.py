from __future__ import annotations

import time
from collections.abc import Callable

from commute_podcast.observability import log_event


def is_transient_provider_error(error: Exception) -> bool:
    transient_types = (ConnectionError, TimeoutError)
    transient_names = {
        "APIConnectionError",
        "APITimeoutError",
        "InternalServerError",
        "RateLimitError",
        "ServiceUnavailableError",
    }
    return isinstance(error, transient_types) or type(error).__name__ in transient_names


def retry_transient[T](
    operation: Callable[[], T],
    *,
    attempts: int,
    base_delay_seconds: float,
    episode_id: str,
    chunk_id: int,
    sleep: Callable[[float], None] = time.sleep,
) -> T:
    last_error: Exception | None = None
    for attempt in range(1, attempts + 1):
        try:
            return operation()
        except Exception as error:
            last_error = error
            if not is_transient_provider_error(error) or attempt == attempts:
                raise
            delay = base_delay_seconds * (2 ** (attempt - 1))
            log_event(
                "provider_retry",
                episode_id=episode_id,
                chunk_id=chunk_id,
                phase="synthesis",
                attempt=attempt,
            )
            sleep(delay)
    assert last_error is not None
    raise last_error
