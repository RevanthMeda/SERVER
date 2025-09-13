"""
Redis client configuration and cache management.
"""

import json
import pickle
import logging
from datetime import timedelta
from typing import Any, Optional, Union, Dict, List
from functools import wraps

import redis
from flask import current_app

logger = logging.getLogger(__name__)


class RedisClient:
    """Redis client wrapper with enhanced functionality."""
    
    def __init__(self, app=None):
        self.redis_client = None
        self.app = app
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize Redis client with Flask app."""
        self.app = app
        
        # Redis configuration
        redis_config = {
            'host': app.config.get('REDIS_HOST', 'localhost'),
            'port': app.config.get('REDIS_PORT', 6379),
            'db': app.config.get('REDIS_DB', 0),
            'password': app.config.get('REDIS_PASSWORD'),
            'socket_timeout': app.config.get('REDIS_SOCKET_TIMEOUT', 5),
            'socket_connect_timeout': app.config.get('REDIS_SOCKET_CONNECT_TIMEOUT', 5),
            'socket_keepalive': app.config.get('REDIS_SOCKET_KEEPALIVE', True),
            'socket_keepalive_options': app.config.get('REDIS_SOCKET_KEEPALIVE_OPTIONS', {}),
            'max_connections': app.config.get('REDIS_MAX_CONNECTIONS', 50),
            'retry_on_timeout': True,
            'health_check_interval': 30,
            'decode_responses': True,
            'encoding': 'utf-8'
        }
        
        # SSL configuration if enabled
        if app.config.get('REDIS_SSL', False):
            redis_config.update({
                'ssl': True,
                'ssl_cert_reqs': app.config.get('REDIS_SSL_CERT_REQS', 'required'),
                'ssl_ca_certs': app.config.get('REDIS_SSL_CA_CERTS'),
                'ssl_certfile': app.config.get('REDIS_SSL_CERTFILE'),
                'ssl_keyfile': app.config.get('REDIS_SSL_KEYFILE')
            })
        
        try:
            # Create connection pool
            pool = redis.ConnectionPool(**redis_config)
            self.redis_client = redis.Redis(connection_pool=pool)
            
            # Test connection
            self.redis_client.ping()
            logger.info("Redis connection established successfully")
            
        except redis.ConnectionError as e:
            logger.error(f"Failed to connect to Redis: {e}")
            if app.config.get('REDIS_REQUIRED', True):
                raise
            else:
                logger.warning("Redis not available, caching disabled")
                self.redis_client = None
        except Exception as e:
            logger.error(f"Unexpected error connecting to Redis: {e}")
            raise
    
    def is_available(self) -> bool:
        """Check if Redis is available."""
        if not self.redis_client:
            return False
        
        try:
            self.redis_client.ping()
            return True
        except redis.ConnectionError:
            return False
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get value from Redis cache."""
        if not self.is_available():
            return default
        
        try:
            value = self.redis_client.get(key)
            if value is None:
                return default
            
            # Try to deserialize JSON first, then pickle
            try:
                return json.loads(value)
            except (json.JSONDecodeError, TypeError):
                try:
                    return pickle.loads(value.encode('latin1'))
                except (pickle.PickleError, AttributeError):
                    return value
                    
        except redis.RedisError as e:
            logger.error(f"Redis GET error for key '{key}': {e}")
            return default
    
    def set(self, key: str, value: Any, timeout: Optional[Union[int, timedelta]] = None) -> bool:
        """Set value in Redis cache."""
        if not self.is_available():
            return False
        
        try:
            # Serialize value
            if isinstance(value, (dict, list, tuple)):
                serialized_value = json.dumps(value, default=str)
            elif isinstance(value, (str, int, float, bool)):
                serialized_value = json.dumps(value)
            else:
                # Use pickle for complex objects
                serialized_value = pickle.dumps(value).decode('latin1')
            
            # Set with timeout
            if timeout:
                if isinstance(timeout, timedelta):
                    timeout = int(timeout.total_seconds())
                return self.redis_client.setex(key, timeout, serialized_value)
            else:
                return self.redis_client.set(key, serialized_value)
                
        except redis.RedisError as e:
            logger.error(f"Redis SET error for key '{key}': {e}")
            return False
        except (json.JSONEncodeError, pickle.PickleError) as e:
            logger.error(f"Serialization error for key '{key}': {e}")
            return False
    
    def delete(self, *keys: str) -> int:
        """Delete keys from Redis cache."""
        if not self.is_available() or not keys:
            return 0
        
        try:
            return self.redis_client.delete(*keys)
        except redis.RedisError as e:
            logger.error(f"Redis DELETE error for keys {keys}: {e}")
            return 0
    
    def exists(self, key: str) -> bool:
        """Check if key exists in Redis cache."""
        if not self.is_available():
            return False
        
        try:
            return bool(self.redis_client.exists(key))
        except redis.RedisError as e:
            logger.error(f"Redis EXISTS error for key '{key}': {e}")
            return False
    
    def expire(self, key: str, timeout: Union[int, timedelta]) -> bool:
        """Set expiration time for a key."""
        if not self.is_available():
            return False
        
        try:
            if isinstance(timeout, timedelta):
                timeout = int(timeout.total_seconds())
            return self.redis_client.expire(key, timeout)
        except redis.RedisError as e:
            logger.error(f"Redis EXPIRE error for key '{key}': {e}")
            return False
    
    def ttl(self, key: str) -> int:
        """Get time to live for a key."""
        if not self.is_available():
            return -1
        
        try:
            return self.redis_client.ttl(key)
        except redis.RedisError as e:
            logger.error(f"Redis TTL error for key '{key}': {e}")
            return -1
    
    def keys(self, pattern: str = '*') -> List[str]:
        """Get keys matching pattern."""
        if not self.is_available():
            return []
        
        try:
            return self.redis_client.keys(pattern)
        except redis.RedisError as e:
            logger.error(f"Redis KEYS error for pattern '{pattern}': {e}")
            return []
    
    def flushdb(self) -> bool:
        """Clear all keys in current database."""
        if not self.is_available():
            return False
        
        try:
            return self.redis_client.flushdb()
        except redis.RedisError as e:
            logger.error(f"Redis FLUSHDB error: {e}")
            return False
    
    def info(self) -> Dict[str, Any]:
        """Get Redis server information."""
        if not self.is_available():
            return {}
        
        try:
            return self.redis_client.info()
        except redis.RedisError as e:
            logger.error(f"Redis INFO error: {e}")
            return {}


class CacheManager:
    """High-level cache management with namespacing and invalidation."""
    
    def __init__(self, redis_client: RedisClient, namespace: str = 'app'):
        self.redis_client = redis_client
        self.namespace = namespace
        self.default_timeout = timedelta(hours=1)
    
    def _make_key(self, key: str) -> str:
        """Create namespaced cache key."""
        return f"{self.namespace}:{key}"
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get cached value."""
        return self.redis_client.get(self._make_key(key), default)
    
    def set(self, key: str, value: Any, timeout: Optional[Union[int, timedelta]] = None) -> bool:
        """Set cached value."""
        if timeout is None:
            timeout = self.default_timeout
        return self.redis_client.set(self._make_key(key), value, timeout)
    
    def delete(self, *keys: str) -> int:
        """Delete cached values."""
        namespaced_keys = [self._make_key(key) for key in keys]
        return self.redis_client.delete(*namespaced_keys)
    
    def exists(self, key: str) -> bool:
        """Check if cached value exists."""
        return self.redis_client.exists(self._make_key(key))
    
    def invalidate_pattern(self, pattern: str) -> int:
        """Invalidate all keys matching pattern."""
        full_pattern = self._make_key(pattern)
        keys = self.redis_client.keys(full_pattern)
        if keys:
            return self.redis_client.delete(*keys)
        return 0
    
    def invalidate_namespace(self) -> int:
        """Invalidate all keys in namespace."""
        return self.invalidate_pattern('*')
    
    def get_or_set(self, key: str, callable_func, timeout: Optional[Union[int, timedelta]] = None) -> Any:
        """Get cached value or set it using callable."""
        value = self.get(key)
        if value is None:
            value = callable_func()
            self.set(key, value, timeout)
        return value
    
    def get_many(self, keys: List[str]) -> Dict[str, Any]:
        """Get multiple cached values."""
        result = {}
        for key in keys:
            result[key] = self.get(key)
        return result
    
    def set_many(self, mapping: Dict[str, Any], timeout: Optional[Union[int, timedelta]] = None) -> bool:
        """Set multiple cached values."""
        success = True
        for key, value in mapping.items():
            if not self.set(key, value, timeout):
                success = False
        return success
    
    def increment(self, key: str, delta: int = 1) -> Optional[int]:
        """Increment a cached integer value."""
        if not self.redis_client.is_available():
            return None
        
        try:
            return self.redis_client.redis_client.incr(self._make_key(key), delta)
        except redis.RedisError as e:
            logger.error(f"Redis INCR error for key '{key}': {e}")
            return None
    
    def decrement(self, key: str, delta: int = 1) -> Optional[int]:
        """Decrement a cached integer value."""
        if not self.redis_client.is_available():
            return None
        
        try:
            return self.redis_client.redis_client.decr(self._make_key(key), delta)
        except redis.RedisError as e:
            logger.error(f"Redis DECR error for key '{key}': {e}")
            return None


# Global instances
redis_client = RedisClient()
cache_manager = CacheManager(redis_client)


def init_cache(app):
    """Initialize cache with Flask app."""
    redis_client.init_app(app)
    
    # Set up cache managers for different namespaces
    app.cache = cache_manager
    app.session_cache = CacheManager(redis_client, 'session')
    app.api_cache = CacheManager(redis_client, 'api')
    app.query_cache = CacheManager(redis_client, 'query')
    
    # Configure default timeouts
    app.cache.default_timeout = timedelta(
        seconds=app.config.get('CACHE_DEFAULT_TIMEOUT', 3600)
    )
    app.session_cache.default_timeout = timedelta(
        seconds=app.config.get('SESSION_CACHE_TIMEOUT', 86400)
    )
    app.api_cache.default_timeout = timedelta(
        seconds=app.config.get('API_CACHE_TIMEOUT', 300)
    )
    app.query_cache.default_timeout = timedelta(
        seconds=app.config.get('QUERY_CACHE_TIMEOUT', 600)
    )
    
    logger.info("Cache system initialized successfully")