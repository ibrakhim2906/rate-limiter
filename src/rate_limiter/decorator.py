import functools

from rate_limiter import bucket


class RateLimitExceeded(Exception):
    def __init__(self, retry_after):

        self.retry_after = retry_after

        super().__init__(f"rate limit exceeded, retry after {retry_after}")


def rate_limited(rate, capacity=None):

    if capacity is None:
        capacity = rate

    def decorator(func):

        token_bucket = bucket.TokenBucket(rate, capacity)

        @functools.wraps(func)
        async def wrapper(*args, **kwargs):

            result = token_bucket.try_consume()

            if not result["allowed"]:
                raise RateLimitExceeded(result["retry_after"])

            return await func(*args, **kwargs)

        return wrapper

    return decorator
