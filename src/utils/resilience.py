import asyncio
import functools
import inspect
import logging
import random
import time
from collections.abc import Callable
from typing import Any

logger = logging.getLogger(__name__)


def is_rate_limit_error(exception: BaseException) -> bool:
    """Checks if an exception represents a rate limit (HTTP 429) or quota exhaustion."""
    err_str = str(exception).lower()
    rate_limit_indicators = [
        "429",
        "quota exceeded",
        "resource exhausted",
        "rate limit",
        "too many requests",
        "resourceexhausted",
    ]
    return any(ind in err_str for ind in rate_limit_indicators)


def retry_with_backoff(
    max_retries: int = 3,
    initial_delay: float = 1.0,
    backoff_factor: float = 2.0,
    jitter: bool = True,
    retry_predicate: Callable[[BaseException], bool] | None = None,
):
    """Decorator providing exponential backoff with jitter for sync and async callables."""
    predicate = retry_predicate or is_rate_limit_error

    def decorator(func: Callable):
        if inspect.iscoroutinefunction(func):

            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs) -> Any:
                delay = initial_delay
                last_err = None
                for attempt in range(max_retries + 1):
                    try:
                        return await func(*args, **kwargs)
                    except Exception as e:
                        last_err = e
                        if attempt < max_retries and predicate(e):
                            sleep_time = delay * (
                                1 + random.random() * 0.5 if jitter else 1.0
                            )
                            logger.warning(
                                "Rate limit encountered in %s (attempt %d/%d). Retrying in %.2fs. Error: %s",
                                func.__name__,
                                attempt + 1,
                                max_retries,
                                sleep_time,
                                e,
                            )
                            await asyncio.sleep(sleep_time)
                            delay *= backoff_factor
                        else:
                            raise
                if last_err:
                    raise last_err

            return async_wrapper
        else:

            @functools.wraps(func)
            def sync_wrapper(*args, **kwargs) -> Any:
                delay = initial_delay
                last_err = None
                for attempt in range(max_retries + 1):
                    try:
                        return func(*args, **kwargs)
                    except Exception as e:
                        last_err = e
                        if attempt < max_retries and predicate(e):
                            sleep_time = delay * (
                                1 + random.random() * 0.5 if jitter else 1.0
                            )
                            logger.warning(
                                "Rate limit encountered in %s (attempt %d/%d). Retrying in %.2fs. Error: %s",
                                func.__name__,
                                attempt + 1,
                                max_retries,
                                sleep_time,
                                e,
                            )
                            time.sleep(sleep_time)
                            delay *= backoff_factor
                        else:
                            raise
                if last_err:
                    raise last_err

            return sync_wrapper

    return decorator
