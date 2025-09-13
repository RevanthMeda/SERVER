"""
Cache decorators for function and method caching.
"""

import hashlib
import json
import logging
from datetime import timedelta
from functools import wraps
from typing import Any, Callable, Optional, Union

from flask import current_app, request, g

logger = logging.getLogger(__name__)


def cache_key(*args, **kwargs) -> str:
    """Generate cache key from function arguments."""
    # Create a deterministic key from arguments
    key_data = {
        'args': args,
        'kwargs': sorted(kwargs.items()) if kwargs else {}
    }
    
    # Serialize and hash
    key_string = json.dumps(key_data, sort_keys=True, default=str)
    return hashlib.md5(key_string.encode()).hexdigest()


def cached(timeout: Optional[Union[int, timedelta]] = None, 
          key_prefix: str = '', 
          unless: Optional[Callable] = None,
          cache_manager_attr: str = 'cache'):
    """
    Decorator to cache function results.
    
    Args:
        timeout: Cache timeout (seconds or timedelta)
        key_prefix: Prefix for cache key
        unless: Function that returns True to skip caching
        cache_manager_attr: Attribute name for cache manager on current_app
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Check if caching should be skipped
            if unless and unless():
                return func(*args, **kwargs)
            
            # Get cache manager
            try:
                cache_mgr = getattr(current_app, cache_manager_attr)
            except (AttributeError, RuntimeError):
                # No app context or cache manager, execute function directly
                return func(*args, **kwargs)
            
            # Generate cache key
            func_key = f"{key_prefix}{func.__name__}:{cache_key(*args, **kwargs)}"
            
            # Try to get from cache
            cached_result = cache_mgr.get(func_key)
            if cached_result is not None:
                logger.debug(f"Cache hit for key: {func_key}")
                return cached_result
            
            # Execute function and cache result
            logger.debug(f"Cache miss for key: {func_key}")
            result = func(*args, **kwargs)
            
            # Cache the result
            cache_mgr.set(func_key, result, timeout)
            
            return result
        
        # Add cache management methods to the decorated function
        wrapper.cache_key = lambda *args, **kwargs: f"{key_prefix}{func.__name__}:{cache_key(*args, **kwargs)}"
        wrapper.invalidate = lambda *args, **kwargs: getattr(current_app, cache_manager_attr).delete(
            wrapper.cache_key(*args, **kwargs)
        )
        
        return wrapper
    return decorator


def cached_property(timeout: Optional[Union[int, timedelta]] = None,
                   key_prefix: str = ''):
    """
    Decorator to cache property results on instances.
    
    Args:
        timeout: Cache timeout (seconds or timedelta)
        key_prefix: Prefix for cache key
    """
    def decorator(func: Callable) -> property:
        @wraps(func)
        def wrapper(self):
            # Generate instance-specific cache key
            instance_id = getattr(self, 'id', id(self))
            func_key = f"{key_prefix}{self.__class__.__name__}:{instance_id}:{func.__name__}"
            
            try:
                cache_mgr = current_app.cache
                
                # Try to get from cache
                cached_result = cache_mgr.get(func_key)
                if cached_result is not None:
                    return cached_result
                
                # Execute function and cache result
                result = func(self)
                cache_mgr.set(func_key, result, timeout)
                
                return result
                
            except (AttributeError, RuntimeError):
                # No app context or cache manager, execute function directly
                return func(self)
        
        return property(wrapper)
    return decorator


def cache_unless_authenticated(unless: Optional[Callable] = None):
    """Skip caching if user is authenticated."""
    def check_auth():
        if unless and unless():
            return True
        
        # Check if user is authenticated
        try:
            from flask_login import current_user
            return current_user.is_authenticated
        except ImportError:
            # Flask-Login not available, check session
            from flask import session
            return 'user_id' in session
        except:
            return False
    
    return check_auth


def cache_per_user(timeout: Optional[Union[int, timedelta]] = None,
                  key_prefix: str = ''):
    """
    Cache decorator that creates user-specific cache keys.
    
    Args:
        timeout: Cache timeout (seconds or timedelta)
        key_prefix: Prefix for cache key
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                cache_mgr = current_app.cache
                
                # Get user identifier
                user_id = 'anonymous'
                try:
                    from flask_login import current_user
                    if current_user.is_authenticated:
                        user_id = current_user.id
                except ImportError:
                    # Flask-Login not available, check session
                    from flask import session
                    user_id = session.get('user_id', 'anonymous')
                except:
                    pass
                
                # Generate user-specific cache key
                func_key = f"{key_prefix}user:{user_id}:{func.__name__}:{cache_key(*args, **kwargs)}"
                
                # Try to get from cache
                cached_result = cache_mgr.get(func_key)
                if cached_result is not None:
                    return cached_result
                
                # Execute function and cache result
                result = func(*args, **kwargs)
                cache_mgr.set(func_key, result, timeout)
                
                return result
                
            except (AttributeError, RuntimeError):
                # No app context or cache manager, execute function directly
                return func(*args, **kwargs)
        
        return wrapper
    return decorator


def cache_response(timeout: Optional[Union[int, timedelta]] = None,
                  key_prefix: str = 'response:',
                  vary_on: Optional[list] = None):
    """
    Cache HTTP response decorator for Flask routes.
    
    Args:
        timeout: Cache timeout (seconds or timedelta)
        key_prefix: Prefix for cache key
        vary_on: List of request attributes to include in cache key
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                cache_mgr = current_app.api_cache
                
                # Build cache key from request
                key_parts = [func.__name__]
                
                # Add URL path
                key_parts.append(request.path)
                
                # Add query parameters
                if request.args:
                    key_parts.append(str(sorted(request.args.items())))
                
                # Add custom vary_on attributes
                if vary_on:
                    for attr in vary_on:
                        if hasattr(request, attr):
                            key_parts.append(str(getattr(request, attr)))
                
                # Add user context if authenticated
                try:
                    from flask_login import current_user
                    if current_user.is_authenticated:
                        key_parts.append(f"user:{current_user.id}")
                except:
                    pass
                
                func_key = f"{key_prefix}{':'.join(key_parts)}"
                func_key = hashlib.md5(func_key.encode()).hexdigest()
                
                # Try to get from cache
                cached_result = cache_mgr.get(func_key)
                if cached_result is not None:
                    logger.debug(f"Response cache hit for: {request.path}")
                    return cached_result
                
                # Execute function and cache result
                logger.debug(f"Response cache miss for: {request.path}")
                result = func(*args, **kwargs)
                
                # Only cache successful responses
                if hasattr(result, 'status_code'):
                    if result.status_code == 200:
                        cache_mgr.set(func_key, result, timeout)
                else:
                    # Assume success for non-Response objects
                    cache_mgr.set(func_key, result, timeout)
                
                return result
                
            except (AttributeError, RuntimeError):
                # No app context or cache manager, execute function directly
                return func(*args, **kwargs)
        
        return wrapper
    return decorator


def invalidate_cache_pattern(pattern: str, cache_manager_attr: str = 'cache'):
    """
    Decorator to invalidate cache patterns after function execution.
    
    Args:
        pattern: Cache key pattern to invalidate
        cache_manager_attr: Attribute name for cache manager on current_app
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)
            
            # Invalidate cache pattern after successful execution
            try:
                cache_mgr = getattr(current_app, cache_manager_attr)
                invalidated = cache_mgr.invalidate_pattern(pattern)
                logger.debug(f"Invalidated {invalidated} cache keys matching pattern: {pattern}")
            except (AttributeError, RuntimeError):
                pass
            
            return result
        
        return wrapper
    return decorator


def cache_memoize(timeout: Optional[Union[int, timedelta]] = None):
    """
    Simple memoization decorator using application cache.
    
    Args:
        timeout: Cache timeout (seconds or timedelta)
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                cache_mgr = current_app.cache
                
                # Generate cache key
                func_key = f"memoize:{func.__module__}.{func.__name__}:{cache_key(*args, **kwargs)}"
                
                # Try to get from cache
                cached_result = cache_mgr.get(func_key)
                if cached_result is not None:
                    return cached_result
                
                # Execute function and cache result
                result = func(*args, **kwargs)
                cache_mgr.set(func_key, result, timeout)
                
                return result
                
            except (AttributeError, RuntimeError):
                # No app context or cache manager, execute function directly
                return func(*args, **kwargs)
        
        return wrapper
    return decorator