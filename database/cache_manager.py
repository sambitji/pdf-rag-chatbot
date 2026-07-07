"""Cache management using Redis."""
import json
import hashlib
from typing import Any, Optional
from datetime import timedelta
from utils.config import config
from utils.logger import get_logger
from utils.error_handlers import CacheError

logger = get_logger(__name__)

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    logger.warning("Redis not available - caching disabled")


class CacheManager:
    """Manage caching with Redis."""
    
    def __init__(
        self,
        host: str = None,
        port: int = None,
        password: str = None,
        ttl: int = None
    ):
        """
        Initialize cache manager.
        
        Args:
            host: Redis host
            port: Redis port
            password: Redis password
            ttl: Default TTL in seconds
        """
        self.enabled = config.enable_cache and REDIS_AVAILABLE
        self.ttl = ttl or config.cache_ttl
        
        if self.enabled:
            try:
                self.redis_client = redis.Redis(
                    host=host or config.redis_host,
                    port=port or config.redis_port,
                    password=password or config.redis_password,
                    decode_responses=True
                )
                # Test connection
                self.redis_client.ping()
                logger.info(f"Cache manager initialized (TTL: {self.ttl}s)")
            except Exception as e:
                logger.error(f"Redis connection failed: {e}")
                self.enabled = False
                self.redis_client = None
        else:
            self.redis_client = None
            logger.info("Cache manager disabled")
    
    def _generate_key(self, prefix: str, identifier: str) -> str:
        """Generate cache key."""
        hash_obj = hashlib.md5(identifier.encode())
        return f"{prefix}:{hash_obj.hexdigest()}"
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        if not self.enabled:
            return None
        
        try:
            value = self.redis_client.get(key)
            if value:
                logger.debug(f"Cache hit: {key}")
                return json.loads(value)
            logger.debug(f"Cache miss: {key}")
            return None
        except Exception as e:
            logger.error(f"Cache get error: {e}")
            return None
    
    def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None
    ) -> bool:
        """Set value in cache."""
        if not self.enabled:
            return False
        
        try:
            serialized = json.dumps(value)
            expiry = ttl or self.ttl
            self.redis_client.setex(
                key,
                timedelta(seconds=expiry),
                serialized
            )
            logger.debug(f"Cache set: {key} (TTL: {expiry}s)")
            return True
        except Exception as e:
            logger.error(f"Cache set error: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """Delete key from cache."""
        if not self.enabled:
            return False
        
        try:
            self.redis_client.delete(key)
            logger.debug(f"Cache delete: {key}")
            return True
        except Exception as e:
            logger.error(f"Cache delete error: {e}")
            return False
    
    def clear(self) -> bool:
        """Clear all cache."""
        if not self.enabled:
            return False
        
        try:
            self.redis_client.flushdb()
            logger.info("Cache cleared")
            return True
        except Exception as e:
            logger.error(f"Cache clear error: {e}")
            return False
    
    def get_query_cache(self, query: str) -> Optional[dict]:
        """Get cached query result."""
        key = self._generate_key("query", query)
        return self.get(key)
    
    def set_query_cache(
        self,
        query: str,
        result: dict,
        ttl: Optional[int] = None
    ) -> bool:
        """Cache query result."""
        key = self._generate_key("query", query)
        return self.set(key, result, ttl)
    
    def get_embedding_cache(self, text: str) -> Optional[list]:
        """Get cached embedding."""
        key = self._generate_key("embedding", text)
        return self.get(key)
    
    def set_embedding_cache(
        self,
        text: str,
        embedding: list,
        ttl: Optional[int] = None
    ) -> bool:
        """Cache embedding."""
        key = self._generate_key("embedding", text)
        return self.set(key, embedding, ttl)
    
    def get_stats(self) -> dict:
        """Get cache statistics."""
        if not self.enabled:
            return {'enabled': False}
        
        try:
            info = self.redis_client.info()
            return {
                'enabled': True,
                'keys': self.redis_client.dbsize(),
                'memory_used': info.get('used_memory_human'),
                'hits': info.get('keyspace_hits', 0),
                'misses': info.get('keyspace_misses', 0)
            }
        except Exception as e:
            logger.error(f"Error getting cache stats: {e}")
            return {'enabled': True, 'error': str(e)}