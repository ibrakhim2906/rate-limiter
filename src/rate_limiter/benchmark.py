import threading
import time
from unittest.mock import patch

from rate_limiter.bucket import TokenBucket


class UnsafeTokenBucket(TokenBucket):
    """Same logic as TokenBucket, but skips the lock — for comparison
    only, never use in real code. Used as-is for the overhead
    measurement (no artificial delay, so it reflects true per-call cost).
    """

    def try_consume(self):
        self.refill()

        if self.tokens < 1:
            return {"allowed": False, "retry_after": (1 - self.tokens) / self.rate}

        self.tokens -= 1

        return {"allowed": True, "retry_after": None}


class UnsafeTokenBucketDelayed(UnsafeTokenBucket):
    """Same as UnsafeTokenBucket, with a deliberate sleep between the
    check and the decrement — used only for the correctness/contention
    test, never for the overhead measurement. Without this delay, the
    race window is only a few CPU instructions wide and the GIL's ~5ms
    switch interval rarely lands inside it, so the bug would almost
    never show up in practice even though it's real. The sleep forces
    threads to interleave right at the vulnerable spot so the race is
    reliably observable.
    """

    def try_consume(self):
        self.refill()

        if self.tokens < 1:
            return {"allowed": False, "retry_after": (1 - self.tokens) / self.rate}

        time.sleep(0.0001)
        self.tokens -= 1

        return {"allowed": True, "retry_after": None}


def hammer(bucket, n_threads=20, calls_per_thread=2000):
    """Fire n_threads * calls_per_thread try_consume() calls at `bucket`
    concurrently, and return the total number allowed. Real elapsed time
    is frozen via mocking time.monotonic so that the only possible
    source of an over-capacity result is a genuine race, not legitimate
    refill from wall-clock time passing during the run.
    """
    frozen_now = time.monotonic()
    success = [0]
    lock = threading.Lock()

    def worker():
        local = 0
        for _ in range(calls_per_thread):
            if bucket.try_consume()["allowed"]:
                local += 1
        with lock:
            success[0] += local

    with patch("rate_limiter.bucket.time.monotonic", return_value=frozen_now):
        threads = [threading.Thread(target=worker) for _ in range(n_threads)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

    return success[0]


if __name__ == "__main__":
    print("Correctness under contention (capacity=100, real time frozen):")
    print("  safe  :", hammer(TokenBucket(rate=1000, capacity=100)))
    # unsafe uses the sleep-widened race window, so keep volume smaller
    # to avoid a very long run (each successful call now costs >=0.1ms)
    print(
        "  unsafe:",
        hammer(
            UnsafeTokenBucketDelayed(rate=1000, capacity=100),
            n_threads=20,
            calls_per_thread=200,
        ),
    )

    print("\nPer-call overhead (single-threaded, no contention):")
    for name, cls in [("safe", TokenBucket), ("unsafe", UnsafeTokenBucket)]:
        b = cls(rate=1_000_000, capacity=1_000_000)
        start = time.perf_counter()
        for _ in range(100_000):
            b.try_consume()
        elapsed = time.perf_counter() - start
        print(f"  {name}: {elapsed / 100_000 * 1e6:.3f} µs/call")
