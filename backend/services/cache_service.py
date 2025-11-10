import redis
import json
from typing import Optional, Dict, Any
from app.core.config import settings


class CacheService:
    """
    Service for caching search queries and responses using Redis.
    Improves performance by avoiding redundant LLM calls for common queries.
    """

    def __init__(self):
        # Initialize Redis client
        self.client = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=0,
            decode_responses=True  # Return strings instead of bytes
        )
        # Default TTL: 1 hour (3600 seconds)
        self.default_ttl = 3600

    def _generate_cache_key(self, query: str, mode: str = "hybrid") -> str:
        """
        Generate a cache key for a query.

        Args:
            query: Search query text
            mode: Search mode (hybrid or corpus_only)

        Returns:
            Cache key string
        """
        # Normalize query for consistent caching
        normalized_query = query.lower().strip()
        return f"search:{mode}:{normalized_query}"

    def get_cached_response(self, query: str, mode: str = "hybrid") -> Optional[Dict[str, Any]]:
        """
        Retrieve a cached response for a query.

        Args:
            query: Search query text
            mode: Search mode

        Returns:
            Cached response dict or None if not found
        """
        try:
            cache_key = self._generate_cache_key(query, mode)
            cached_data = self.client.get(cache_key)

            if cached_data:
                return json.loads(cached_data)
            return None

        except Exception as e:
            print(f"Error retrieving from cache: {e}")
            return None

    def cache_response(
        self,
        query: str,
        response: Dict[str, Any],
        mode: str = "hybrid",
        ttl: Optional[int] = None
    ) -> bool:
        """
        Cache a search response.

        Args:
            query: Search query text
            response: Response dict to cache
            mode: Search mode
            ttl: Time to live in seconds (default: 1 hour)

        Returns:
            True if successful, False otherwise
        """
        try:
            cache_key = self._generate_cache_key(query, mode)
            ttl = ttl or self.default_ttl

            # Serialize response to JSON
            cached_data = json.dumps(response)

            # Store in Redis with TTL
            self.client.setex(cache_key, ttl, cached_data)
            return True

        except Exception as e:
            print(f"Error caching response: {e}")
            return False

    def invalidate_cache(self, query: str, mode: str = "hybrid") -> bool:
        """
        Invalidate (delete) a cached response.

        Args:
            query: Search query text
            mode: Search mode

        Returns:
            True if deleted, False otherwise
        """
        try:
            cache_key = self._generate_cache_key(query, mode)
            return self.client.delete(cache_key) > 0
        except Exception as e:
            print(f"Error invalidating cache: {e}")
            return False

    def clear_all_cache(self) -> bool:
        """
        Clear all cached search responses.
        WARNING: This will delete all keys in the Redis database.

        Returns:
            True if successful
        """
        try:
            self.client.flushdb()
            return True
        except Exception as e:
            print(f"Error clearing cache: {e}")
            return False

    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the cache.

        Returns:
            Dict with cache stats (keys count, memory usage, etc.)
        """
        try:
            info = self.client.info()
            return {
                "keys_count": self.client.dbsize(),
                "used_memory_human": info.get("used_memory_human"),
                "connected_clients": info.get("connected_clients"),
                "uptime_in_seconds": info.get("uptime_in_seconds")
            }
        except Exception as e:
            print(f"Error getting cache stats: {e}")
            return {}

    def health_check(self) -> bool:
        """
        Check if Redis connection is healthy.

        Returns:
            True if connection is OK
        """
        try:
            return self.client.ping()
        except Exception as e:
            print(f"Redis health check failed: {e}")
            return False


# Singleton instance
cache_service = CacheService()
