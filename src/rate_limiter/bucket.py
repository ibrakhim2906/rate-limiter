import threading
import time


class TokenBucket:
    def __init__(self, rate: float, capacity: int):

        if rate <= 0:
            raise ValueError("Rate cannot be negative or zero")

        if capacity <= 0:
            raise ValueError("Capacity cannot be negative or zero")

        self.rate = rate
        self.capacity = capacity
        self.tokens = capacity
        self.last_refill = time.monotonic()
        self._lock = threading.Lock()

    # Assume that now will not be given earlier time then self.last_refill
    def refill(self, now=None):

        if now is None:
            now = time.monotonic()

        new_tokens = min(
            self.capacity, self.rate * (now - self.last_refill) + self.tokens
        )
        self.tokens = new_tokens
        self.last_refill = now

    def try_consume(self):

        with self._lock:
            self.refill()

            if self.tokens < 1:
                return {"allowed": False, "retry_after": (1 - self.tokens) / self.rate}

            self.tokens -= 1

            return {"allowed": True, "retry_after": None}
