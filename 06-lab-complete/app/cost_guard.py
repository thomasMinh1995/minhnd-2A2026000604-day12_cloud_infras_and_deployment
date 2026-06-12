"""Monthly cost guard per user backed by Redis."""
from datetime import datetime, timezone

from fastapi import HTTPException

from app.config import settings
from app.redis_client import redis_client


def check_and_record_cost(user_id: str) -> float:
    month = datetime.now(timezone.utc).strftime("%Y-%m")
    key = f"cost:{user_id}:{month}"
    current = float(redis_client.client.get(key) or 0)

    if current + settings.cost_per_request_usd > settings.monthly_budget_usd:
        raise HTTPException(
            status_code=402,
            detail=(
                f"Monthly budget exhausted: ${settings.monthly_budget_usd:.2f}/month "
                f"(current: ${current:.3f})"
            ),
        )

    new_total = redis_client.client.incrbyfloat(key, settings.cost_per_request_usd)
    if new_total == settings.cost_per_request_usd:
        redis_client.client.expire(key, 60 * 60 * 24 * 35)

    return settings.cost_per_request_usd
