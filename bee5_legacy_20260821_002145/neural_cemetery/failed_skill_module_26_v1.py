# ERROR:
# bionic/linker/linker_cfi.cpp:158: MapShadow CHECK 'p != MAP_FAILED' failed

import time
import functools
import random
from typing import Callable, TypeVar, Any, Tuple

T = TypeVar("T")


class RetryError(Exception):
    """Raised when a retried function still fails after all attempts."""
    pass


def retry(
    attempts: int = 3,
    delay: float = 0.1,
    backoff: float = 2.0,
    exceptions: Tuple[Exception, ...] = (Exception,),
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """
    Decorator that retries a function call when specified exceptions occur.

    Args:
        attempts: Number of total attempts (including the initial call).
        delay: Initial delay between attempts in seconds.
        backoff: Multiplicative factor applied to the delay after each failure.
        exceptions: Exception types that trigger a retry.

    Returns:
        Wrapped function with retry logic.
    """

    if attempts < 1:
        raise ValueError("attempts must be at least 1")
    if delay < 0:
        raise ValueError("delay must be non‑negative")
    if backoff < 1:
        raise ValueError("backoff must be >= 1")

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            _delay = delay
            last_exc: Exception | None = None
            for attempt in range(1, attempts + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as exc:
                    last_exc = exc
                    if attempt == attempts:
                        break
                    time.sleep(_delay)
                    _delay *= backoff
            raise RetryError(f"Function {func.__name__} failed after {attempts} attempts") from last_exc

        return wrapper

    return decorator


# Self‑test
if __name__ == "__main__":
    # A flaky function that fails a configurable number of times before succeeding
    class Flaky:
        def __init__(self, fail_times: int):
            self.fail_times = fail_times
            self.calls = 0

        @retry(attempts=5, delay=0.01, backoff=1.5, exceptions=(ValueError,))
        def maybe_fail(self) -> str:
            self.calls += 1
            if self.calls <= self.fail_times:
                raise ValueError("Simulated failure")
            return "success"

    # Test 1: should succeed after 2 failures
    flaky = Flaky(fail_times=2)
    result = flaky.maybe_fail()
    if result != "success" or flaky.calls != 3:
        raise AssertionError("Flaky test failed: incorrect success handling")

    # Test 2: should raise RetryError after exhausting attempts
    flaky2 = Flaky(fail_times=10)
    try:
        flaky2.maybe_fail()
        raise AssertionError("Flaky test failed: expected RetryError")
    except RetryError:
        pass  # Expected

    # Test 3: verify that invalid parameters raise ValueError immediately
    try:
        @retry(attempts=0)
        def dummy():  # pragma: no cover
            return None
        raise AssertionError("Invalid attempts did not raise")
    except ValueError:
        pass

    print("All retry tests passed")