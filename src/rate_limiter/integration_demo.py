import asyncio

import httpx

from rate_limiter.decorator import RateLimitExceeded, rate_limited


@rate_limited(rate=2, capacity=5)
async def get_weather(client: httpx.AsyncClient, call_id: int):
    resp = await client.get(
        "https://api.open-meteo.com/v1/forecast",
        params={"latitude": 51.5, "longitude": -0.1, "current_weather": True},
    )
    return call_id, resp.status_code


async def main():
    async with httpx.AsyncClient() as client:
        tasks = [get_weather(client, i) for i in range(20)]
        results = await asyncio.gather(*tasks, return_exceptions=True)

    allowed = sum(1 for r in results if not isinstance(r, RateLimitExceeded))
    rejected = len(results) - allowed
    print(
        f"{allowed} requests reached the API, {rejected} were rejected locally "
        f"before ever hitting the network"
    )


if __name__ == "__main__":
    asyncio.run(main())
