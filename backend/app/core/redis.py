import json
from typing import Optional, Any
from redis.asyncio import Redis
from app.core.config import settings


class RedisService:
    """Async Redis caching layer."""

    _client: Optional[Redis] = None

    @classmethod
    async def connect(cls) -> None:
        """Initialize the Redis connection."""
        if cls._client is None:
            cls._client = Redis.from_url(
                settings.REDIS_URL,
                decode_responses=True,
            )
            # Verify connection
            await cls._client.ping()

    @classmethod
    async def disconnect(cls) -> None:
        """Close the Redis connection."""
        if cls._client:
            await cls._client.close()
            cls._client = None

    @classmethod
    def get_client(cls) -> Redis:
        """Get the Redis client (must call connect() first)."""
        if cls._client is None:
            raise RuntimeError("Redis not connected. Call RedisService.connect() first.")
        return cls._client

    @classmethod
    async def get(cls, key: str) -> Optional[Any]:
        """Get a value from cache."""
        client = cls.get_client()
        value = await client.get(key)
        if value is None:
            return None
        try:
            return json.loads(value)
        except (json.JSONDecodeError, TypeError):
            return value

    @classmethod
    async def set(cls, key: str, value: Any, ttl_seconds: int = 300) -> None:
        """Set a value in cache with TTL"""
        client = cls.get_client()
        serialized = json.dumps(value) if not isinstance(value, str) else value
        await client.set(key, serialized, ex=ttl_seconds)

    @classmethod
    async def delete(cls, key: str) -> None:
        """Delete a key from cache."""
        client = cls.get_client()
        await client.delete(key)

    @classmethod
    async def delete_pattern(cls, pattern: str) -> None:
        """Delete all keys matching a pattern"""
        client = cls.get_client()
        cursor = 0
        while True:
            cursor, keys = await client.scan(cursor, match=pattern, count=100)
            if keys:
                await client.delete(*keys)
            if cursor == 0:
                break

    @classmethod
    async def exists(cls, key: str) -> bool:
        """Check if a key exists."""
        client = cls.get_client()
        return await client.exists(key) > 0

def user_stats_key(user_id: int) -> str:
    return f"user:{user_id}:stats"

def user_attempts_key(user_id: int, problem_id: Optional[int] = None) -> str:
    if problem_id:
        return f"user:{user_id}:attempts:problem:{problem_id}"
    return f"user:{user_id}:attempts:recent"

def attempt_summary_key(attempt_id: int) -> str:
    return f"attempt:{attempt_id}:telemetry_summary"