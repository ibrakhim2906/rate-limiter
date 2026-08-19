# Token Bucket Rate Limiter

Async decorator, token bucket algorithm, safe across threads and event
loops.

```python
@rate_limited(rate=5, capacity=10)
async def call_api(...):
    ...

try:
    await call_api(...)
except RateLimitExceeded as e:
    print(f"retry in {e.retry_after:.2f}s")
```

## The interesting part

Has to stay correct when called from multiple threads, each possibly
running its own event loop — so `asyncio.Lock` was out (it only
coordinates coroutines on one loop). Used a plain `threading.Lock`
instead; safe here since the protected section is pure arithmetic and
never awaits.

Proved it instead of just asserting it: `benchmark.py` hammers the
bucket from 20 threads with real time frozen. With the lock: exactly
100/100. Without it: 115 — double-spent tokens from threads that both
saw "available" before either wrote back its decrement. Lock overhead:
~0.1µs/call.

## Other choices

- Rejects immediately, never waits — caller handles retry/backoff via
  `retry_after`
- Each decorated function gets its own bucket
- Lazy refill, no background timer — just computes elapsed time per call

## Testing

`pytest test/ -v`. `test_multithreading_stampede.py` is written to fail
if the lock is removed, not just pass regardless.

`integration_demo.py` hits a real weather API with `rate=2, capacity=5`
and fires 20 concurrent requests: 5 got through, 15 were rejected before
touching the network.

## Limitations

Single process only. No fairness guarantee under contention. One token
per call.
