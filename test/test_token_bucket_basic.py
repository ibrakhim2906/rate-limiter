from rate_limiter import bucket


def test_token_refill_with_no_cap_hit():

    token_bucket = bucket.TokenBucket(5.0, 20)

    token_bucket.tokens = 5
    token_bucket.last_refill = 0

    token_bucket.refill(now=1)

    assert token_bucket.tokens == 10


def test_token_refill_do_not_overflow():

    token_bucket = bucket.TokenBucket(rate=5.0, capacity=20)

    token_bucket.tokens = 5
    token_bucket.last_refill = 0

    token_bucket.refill(now=100)

    assert token_bucket.tokens == 20


def test_token_no_time_elapsed_no_refill():

    token_bucket = bucket.TokenBucket(rate=6.7, capacity=10)

    token_bucket.tokens = 5
    token_bucket.last_refill = 0

    token_bucket.refill(now=0)

    assert token_bucket.tokens == 5
