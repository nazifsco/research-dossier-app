"""
Redis client for caching and rate limiting.
Includes in-memory fallback for development without Redis.
"""

import json
import time
from typing import Optional, Any, Dict, Tuple
from functools import wraps
import redis
from app.config import get_settings

settings = get_settings()

# Redis client (lazy initialization)
_redis_client: Optional[redis.Redis] = None

# In-memory fallback storage: key -> (value, expiry_timestamp)
_memory_store: Dict[str, Tuple[Any, float]] = {}


def _memory_get(key: str) -> Optional[Any]:
    """Get value from memory store, respecting TTL."""
    if key in _memory_store:
        value, expiry = _memory_store[key]
        if time.time() < expiry:
            return value
        else:
            del _memory_store[key]
    return None


def _memory_set(key: str, value: Any, ttl: int) -> bool:
    """Set value in memory store with TTL."""
    _memory_store[key] = (value, time.time() + ttl)
    return True


def _memory_delete(key: str) -> bool:
    """Delete value from memory store."""
    if key in _memory_store:
        del _memory_store[key]
    return True


def get_redis() -> Optional[redis.Redis]:
    """Get Redis client, initializing if needed."""
    global _redis_client

    if _redis_client is None and settings.redis_url:
        try:
            _redis_client = redis.from_url(
                settings.redis_url,
                decode_responses=True,
                socket_connect_timeout=5
            )
            # Test connection
            _redis_client.ping()
        except redis.ConnectionError:
            print("[Redis] Connection failed - caching disabled")
            _redis_client = None

    return _redis_client


class Cache:
    """Simple caching utilities with in-memory fallback."""

    @staticmethod
    def get(key: str) -> Optional[Any]:
        """Get a cached value."""
        cache_key = f"cache:{key}"
        client = get_redis()

        if client:
            try:
                data = client.get(cache_key)
                return json.loads(data) if data else None
            except:
                pass

        # Fallback to memory
        return _memory_get(cache_key)

    @staticmethod
    def set(key: str, value: Any, ttl: int = 300) -> bool:
        """Set a cached value with TTL in seconds."""
        cache_key = f"cache:{key}"
        client = get_redis()

        if client:
            try:
                client.setex(cache_key, ttl, json.dumps(value))
                return True
            except:
                pass

        # Fallback to memory
        return _memory_set(cache_key, value, ttl)

    @staticmethod
    def delete(key: str) -> bool:
        """Delete a cached value."""
        cache_key = f"cache:{key}"
        client = get_redis()

        if client:
            try:
                client.delete(cache_key)
                return True
            except:
                pass

        # Fallback to memory
        return _memory_delete(cache_key)


class RateLimiter:
    """Rate limiting utilities."""

    @staticmethod
    def is_allowed(key: str, max_requests: int, window_seconds: int) -> bool:
        """
        Check if request is allowed under rate limit.

        Args:
            key: Unique identifier (e.g., user_id, ip_address)
            max_requests: Maximum requests allowed
            window_seconds: Time window in seconds

        Returns:
            True if allowed, False if rate limited
        """
        client = get_redis()
        if not client:
            # If Redis unavailable, allow all requests
            return True

        try:
            redis_key = f"ratelimit:{key}"
            current = client.incr(redis_key)

            if current == 1:
                client.expire(redis_key, window_seconds)

            return current <= max_requests
        except:
            return True

    @staticmethod
    def get_remaining(key: str, max_requests: int) -> int:
        """Get remaining requests in current window."""
        client = get_redis()
        if not client:
            return max_requests

        try:
            current = client.get(f"ratelimit:{key}")
            if current is None:
                return max_requests
            return max(0, max_requests - int(current))
        except:
            return max_requests


def cached(ttl: int = 300, key_prefix: str = ""):
    """
    Decorator to cache function results.

    Usage:
        @cached(ttl=60, key_prefix="user")
        async def get_user(user_id: str):
            ...
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Build cache key from function name and arguments
            cache_key = f"{key_prefix}:{func.__name__}:{hash(str(args) + str(kwargs))}"

            # Try to get from cache
            cached_value = Cache.get(cache_key)
            if cached_value is not None:
                return cached_value

            # Execute function
            result = await func(*args, **kwargs)

            # Cache result
            Cache.set(cache_key, result, ttl)

            return result
        return wrapper
    return decorator
