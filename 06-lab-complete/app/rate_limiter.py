"""Per-user rate limiting backed by Redis."""
from datetime import datetime, timezone

from fastapi import HTTPException

from app.config import settings
from app.redis_client import redis_client


def check_rate_limit(user_id: str) -> None:
    minute = datetime.now(timezone.utc).strftime("%Y%m%d%H%M")
    key = f"rate:{user_id}:{minute}"
    count = redis_client.client.incr(key)
    if count == 1:
        redis_client.client.expire(key, 60)

    if count > settings.rate_limit_per_minute:
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit exceeded: {settings.rate_limit_per_minute} requests/minute",
            headers={"Retry-After": "60"},
        )
