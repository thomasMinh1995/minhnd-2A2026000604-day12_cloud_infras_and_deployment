"""Redis client with in-memory fallback for local tests without Redis."""
from __future__ import annotations

import json
import time
from typing import Any

import redis

from app.config import settings


class MemoryRedis:
    """Minimal Redis-like store for development and unit tests."""

    def __init__(self) -> None:
        self._data: dict[str, Any] = {}
        self._expiry: dict[str, float] = {}

    def _purge_expired(self, key: str) -> None:
        if key in self._expiry and self._expiry[key] <= time.time():
            self._data.pop(key, None)
            self._expiry.pop(key, None)

    def ping(self) -> bool:
        return True

    def get(self, key: str) -> str | None:
        self._purge_expired(key)
        value = self._data.get(key)
        return str(value) if value is not None else None

    def set(self, key: str, value: str) -> None:
        self._data[key] = value

    def setex(self, key: str, ttl_seconds: int, value: str) -> None:
        self._data[key] = value
        self._expiry[key] = time.time() + ttl_seconds

    def incr(self, key: str) -> int:
        self._purge_expired(key)
        current = int(float(self._data.get(key, 0)))
        current += 1
        self._data[key] = current
        return current

    def expire(self, key: str, ttl_seconds: int) -> None:
        self._expiry[key] = time.time() + ttl_seconds

    def incrbyfloat(self, key: str, amount: float) -> float:
        self._purge_expired(key)
        current = float(self._data.get(key, 0))
        current += amount
        self._data[key] = current
        return current


class RedisClient:
    def __init__(self) -> None:
        self._client: redis.Redis | MemoryRedis | None = None
        self.using_memory = False

    def connect(self) -> None:
        if not settings.redis_url:
            self._client = MemoryRedis()
            self.using_memory = True
            return

        try:
            client = redis.from_url(settings.redis_url, decode_responses=True)
            client.ping()
            self._client = client
            self.using_memory = False
        except Exception:
            if settings.environment in ("development", "test"):
                self._client = MemoryRedis()
                self.using_memory = True
            else:
                raise

    @property
    def client(self) -> redis.Redis | MemoryRedis:
        if self._client is None:
            raise RuntimeError("Redis client not connected")
        return self._client

    def ping(self) -> bool:
        if self._client is None:
            return False
        return bool(self._client.ping())

    def get_json(self, key: str) -> Any:
        raw = self.client.get(key)
        return json.loads(raw) if raw else None

    def set_json(self, key: str, value: Any, ttl_seconds: int | None = None) -> None:
        payload = json.dumps(value)
        if ttl_seconds:
            self.client.setex(key, ttl_seconds, payload)
        else:
            self.client.set(key, payload)


redis_client = RedisClient()
