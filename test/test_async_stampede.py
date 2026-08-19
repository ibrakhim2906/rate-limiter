import asyncio

from rate_limiter.decorator import RateLimitExceeded, rate_limited


@rate_limited(1, 20)
async def ping():
    return "ok"


async def test_single_event_async_stampede():

    tasks = [ping() for _ in range(100)]

    action = await asyncio.gather(*tasks, return_exceptions=True)

    success_count = 0
    failures_count = 0

    for result in action:
        if not isinstance(result, RateLimitExceeded):
            success_count += 1

        else:
            failures_count += 1

    assert success_count == 20
    assert failures_count == 80
