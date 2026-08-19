import asyncio
import threading
import time
from unittest.mock import patch

from rate_limiter.decorator import RateLimitExceeded, rate_limited


@rate_limited(5, 100)
async def ping():
    return "ok"


class SafeCounter:
    def __init__(self):

        self.success = 0
        self.failures = 0
        self._lock = threading.Lock()

    def record(self, is_success: bool):

        with self._lock:
            if is_success:
                self.success += 1
            else:
                self.failures += 1


def thread_worker(counter: SafeCounter, calls_per_thread: int):

    async def inner():

        tasks = [ping() for _ in range(calls_per_thread)]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        for result in results:
            counter.record(is_success=not isinstance(result, RateLimitExceeded))

    asyncio.run(inner())


def test_multi_thread_stampede():
    frozen_now = time.monotonic()

    with patch("rate_limiter.bucket.time.monotonic", return_value=frozen_now):
        counter = SafeCounter()
        threads = [
            threading.Thread(target=thread_worker, args=(counter, 200))
            for _ in range(50)
        ]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

    assert counter.success == 100
    assert counter.failures == 9900
