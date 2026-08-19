import time

import pytest

from rate_limiter import bucket


def test_full_bucket_consume_succeed():

    token_bucket = bucket.TokenBucket(rate=5.0, capacity=10)

    result = token_bucket.try_consume()

    assert result["allowed"] is True
    assert token_bucket.tokens == 9


def test_bucket_drains_then_rejects():

    token_bucket = bucket.TokenBucket(rate=5.0, capacity=10)

    for _ in range(10):
        result = token_bucket.try_consume()
        assert result["allowed"] is True

    result = token_bucket.try_consume()
    assert result["allowed"] is False


def test_bucket_time_passed_consume_succeed():

    token_bucket = bucket.TokenBucket(rate=3.0, capacity=10)

    for i in range(10):
        token_bucket.try_consume()

    result = token_bucket.try_consume()

    assert result["allowed"] is False

    time.sleep(1.0)

    result = token_bucket.try_consume()

    assert result["allowed"] is True


def test_retry_after_exact_value():
    token_bucket = bucket.TokenBucket(rate=5.0, capacity=10)
    token_bucket.tokens = 0.0

    result = token_bucket.try_consume()

    assert result["retry_after"] == pytest.approx(0.2, abs=1e-3)
