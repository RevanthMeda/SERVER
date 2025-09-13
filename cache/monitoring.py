"""
Cache monitoring and performance utilities.
"""

import time
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from functools import wraps

from flask import current_app, request, g

logger = logging.getLogger(__name__)


class CacheMonitor:
    """Monitor cache performance and usage."""
    
    def __init__(self, redis_client):
        self.redis_client = redis_client
        self.stats_key = 'cache:stats'
        self.performance_key = 'cache:performance'
    
    def record_hit(self, key: str, response_time: float = None):
        """Record a cache hit."""
        if not self.redis_client.is_available():
            return
        
        try:
            # Increment hit counter
            self.redis_client.redis_client.hincrby(self.stats_key, 'hits', 1)
            self.redis_client.redis_client.hincrby(f"{self.stats_key}:keys", key, 1)
            
            # Record response time if provided
            if response_time is not None:
                self.redis_client.redis_client.lpush(
                    f"{self.performance_key}:hit_times", 
                    f"{time.time()}:{response_time}"
                )
                # Keep only last 1000 entries
                self.redis_client.redis_client.ltrim(f"{self.performance_key}:hit_times", 0, 999)
                
        except Exception as e:
            logger.error(f"Error recording cache hit: {e}")
    
    def record_miss(self, key: str, response_time: float = None):
        """Record a cache miss."""
        if not self.redis_client.is_available():
            return
        
        try:
            # Increment miss counter
            self.redis_client.redis_client.hincrby(self.stats_key, 'misses', 1)
            self.redis_client.redis_client.hincrby(f"{self.stats_key}:miss_keys", key, 1)
            
            # Record response time if provided
            if response_time is not None:
                self.redis_client.redis_client.lpush(
                    f"{self.performance_key}:miss_times", 
                    f"{time.time()}:{response_time}"
                )
                # Keep only last 1000 entries
                self.redis_client.redis_client.ltrim(f"{self.performance_key}:miss_times", 0, 999)
                
        except Exception as e:
            logger.error(f"Error recording cache miss: {e}")
    
    def record_set(self, key: str, size: int = None):
        """Record a cache set operation."""
        if not self.redis_client.is_available():
            return
        
        try:
            # Increment set counter
            self.redis_client.redis_client.hincrby(self.stats_key, 'sets', 1)
            
            # Record size if provided
            if size is not None:
                self.redis_client.redis_client.hincrby(self.stats_key, 'total_size', size)
                
        except Exception as e:
            logger.error(f"Error recording cache set: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        if not self.redis_client.is_available():
            return {'error': 'Redis not available'}
        
        try:
            # Get basic stats
            stats = self.redis_client.redis_client.hgetall(self.stats_key)
            
            # Convert to integers
            for key in ['hits', 'misses', 'sets', 'total_size']:
                stats[key] = int(stats.get(key, 0))
            
            # Calculate hit rate
            total_requests = stats['hits'] + stats['misses']
            stats['hit_rate'] = (stats['hits'] / total_requests * 100) if total_requests > 0 else 0
            
            # Get Redis info
            redis_info = self.redis_client.info()
            stats['redis_info'] = {
                'used_memory': redis_info.get('used_memory_human', 'N/A'),
                'connected_clients': redis_info.get('connected_clients', 0),
                'total_commands_processed': redis_info.get('total_commands_processed', 0),
                'keyspace_hits': redis_info.get('keyspace_hits', 0),
                'keyspace_misses': redis_info.get('keyspace_misses', 0)
            }
            
            # Calculate Redis hit rate
            redis_hits = redis_info.get('keyspace_hits', 0)
            redis_misses = redis_info.get('keyspace_misses', 0)
            redis_total = redis_hits + redis_misses
            stats['redis_hit_rate'] = (redis_hits / redis_total * 100) if redis_total > 0 else 0
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting cache stats: {e}")
            return {'error': str(e)}
    
    def get_top_keys(self, limit: int = 10) -> Dict[str, List]:
        """Get most frequently accessed keys."""
        if not self.redis_client.is_available():
            return {'hit_keys': [], 'miss_keys': []}
        
        try:
            # Get top hit keys
            hit_keys = self.redis_client.redis_client.hgetall(f"{self.stats_key}:keys")
            hit_keys = sorted(hit_keys.items(), key=lambda x: int(x[1]), reverse=True)[:limit]
            
            # Get top miss keys
            miss_keys = self.redis_client.redis_client.hgetall(f"{self.stats_key}:miss_keys")
            miss_keys = sorted(miss_keys.items(), key=lambda x: int(x[1]), reverse=True)[:limit]
            
            return {
                'hit_keys': [{'key': k, 'count': int(v)} for k, v in hit_keys],
                'miss_keys': [{'key': k, 'count': int(v)} for k, v in miss_keys]
            }
            
        except Exception as e:
            logger.error(f"Error getting top keys: {e}")
            return {'hit_keys': [], 'miss_keys': []}
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get cache performance metrics."""
        if not self.redis_client.is_available():
            return {'error': 'Redis not available'}
        
        try:
            # Get recent hit times
            hit_times = self.redis_client.redis_client.lrange(f"{self.performance_key}:hit_times", 0, 99)
            miss_times = self.redis_client.redis_client.lrange(f"{self.performance_key}:miss_times", 0, 99)
            
            # Parse and calculate averages
            hit_response_times = []
            for entry in hit_times:
                try:
                    timestamp, response_time = entry.split(':')
                    hit_response_times.append(float(response_time))
                except (ValueError, AttributeError):
                    continue
            
            miss_response_times = []
            for entry in miss_times:
                try:
                    timestamp, response_time = entry.split(':')
                    miss_response_times.append(float(response_time))
                except (ValueError, AttributeError):
                    continue
            
            return {
                'avg_hit_time': sum(hit_response_times) / len(hit_response_times) if hit_response_times else 0,
                'avg_miss_time': sum(miss_response_times) / len(miss_response_times) if miss_response_times else 0,
                'hit_samples': len(hit_response_times),
                'miss_samples': len(miss_response_times)
            }
            
        except Exception as e:
            logger.error(f"Error getting performance metrics: {e}")
            return {'error': str(e)}
    
    def reset_stats(self):
        """Reset cache statistics."""
        if not self.redis_client.is_available():
            return False
        
        try:
            # Delete all stats keys
            keys_to_delete = [
                self.stats_key,
                f"{self.stats_key}:keys",
                f"{self.stats_key}:miss_keys",
                f"{self.performance_key}:hit_times",
                f"{self.performance_key}:miss_times"
            ]
            
            self.redis_client.delete(*keys_to_delete)
            return True
            
        except Exception as e:
            logger.error(f"Error resetting cache stats: {e}")
            return False


def monitor_cache_performance(cache_manager_attr: str = 'cache'):
    """
    Decorator to monitor cache performance for functions.
    
    Args:
        cache_manager_attr: Attribute name for cache manager on current_app
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            
            try:
                result = func(*args, **kwargs)
                response_time = time.time() - start_time
                
                # Record performance metrics
                try:
                    cache_mgr = getattr(current_app, cache_manager_attr)
                    if hasattr(cache_mgr, 'monitor'):
                        # This would be set up in the cache manager
                        cache_mgr.monitor.record_hit(func.__name__, response_time)
                except (AttributeError, RuntimeError):
                    pass
                
                return result
                
            except Exception as e:
                response_time = time.time() - start_time
                
                # Record error metrics
                try:
                    cache_mgr = getattr(current_app, cache_manager_attr)
                    if hasattr(cache_mgr, 'monitor'):
                        cache_mgr.monitor.record_miss(func.__name__, response_time)
                except (AttributeError, RuntimeError):
                    pass
                
                raise
        
        return wrapper
    return decorator


class CacheHealthChecker:
    """Check cache system health and performance."""
    
    def __init__(self, redis_client):
        self.redis_client = redis_client
    
    def check_connection(self) -> Dict[str, Any]:
        """Check Redis connection health."""
        try:
            start_time = time.time()
            self.redis_client.redis_client.ping()
            response_time = time.time() - start_time
            
            return {
                'status': 'healthy',
                'response_time': response_time,
                'message': 'Redis connection is healthy'
            }
            
        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e),
                'message': 'Redis connection failed'
            }
    
    def check_memory_usage(self) -> Dict[str, Any]:
        """Check Redis memory usage."""
        try:
            info = self.redis_client.info()
            used_memory = info.get('used_memory', 0)
            max_memory = info.get('maxmemory', 0)
            
            if max_memory > 0:
                memory_usage_percent = (used_memory / max_memory) * 100
                status = 'healthy' if memory_usage_percent < 80 else 'warning' if memory_usage_percent < 95 else 'critical'
            else:
                memory_usage_percent = 0
                status = 'healthy'
            
            return {
                'status': status,
                'used_memory': used_memory,
                'used_memory_human': info.get('used_memory_human', 'N/A'),
                'max_memory': max_memory,
                'memory_usage_percent': memory_usage_percent,
                'message': f'Memory usage: {memory_usage_percent:.1f}%'
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e),
                'message': 'Failed to check memory usage'
            }
    
    def check_performance(self) -> Dict[str, Any]:
        """Check Redis performance metrics."""
        try:
            info = self.redis_client.info()
            
            # Get key performance metrics
            keyspace_hits = info.get('keyspace_hits', 0)
            keyspace_misses = info.get('keyspace_misses', 0)
            total_commands = info.get('total_commands_processed', 0)
            
            # Calculate hit rate
            total_keyspace_ops = keyspace_hits + keyspace_misses
            hit_rate = (keyspace_hits / total_keyspace_ops * 100) if total_keyspace_ops > 0 else 0
            
            # Determine status based on hit rate
            if hit_rate >= 90:
                status = 'excellent'
            elif hit_rate >= 70:
                status = 'good'
            elif hit_rate >= 50:
                status = 'fair'
            else:
                status = 'poor'
            
            return {
                'status': status,
                'hit_rate': hit_rate,
                'keyspace_hits': keyspace_hits,
                'keyspace_misses': keyspace_misses,
                'total_commands': total_commands,
                'connected_clients': info.get('connected_clients', 0),
                'message': f'Hit rate: {hit_rate:.1f}%'
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e),
                'message': 'Failed to check performance metrics'
            }
    
    def run_health_check(self) -> Dict[str, Any]:
        """Run comprehensive health check."""
        connection_health = self.check_connection()
        memory_health = self.check_memory_usage()
        performance_health = self.check_performance()
        
        # Determine overall status
        statuses = [connection_health['status'], memory_health['status'], performance_health['status']]
        
        if 'unhealthy' in statuses or 'error' in statuses:
            overall_status = 'unhealthy'
        elif 'critical' in statuses:
            overall_status = 'critical'
        elif 'warning' in statuses:
            overall_status = 'warning'
        else:
            overall_status = 'healthy'
        
        return {
            'overall_status': overall_status,
            'timestamp': datetime.utcnow().isoformat(),
            'checks': {
                'connection': connection_health,
                'memory': memory_health,
                'performance': performance_health
            }
        }


def init_cache_monitoring(app):
    """Initialize cache monitoring for the application."""
    if hasattr(app, 'cache') and app.cache.redis_client.is_available():
        # Add monitor to cache manager
        app.cache.monitor = CacheMonitor(app.cache.redis_client)
        app.cache.health_checker = CacheHealthChecker(app.cache.redis_client)
        
        # Add health check endpoint
        @app.route('/api/cache/health')
        def cache_health():
            """Cache health check endpoint."""
            health_check = app.cache.health_checker.run_health_check()
            status_code = 200 if health_check['overall_status'] in ['healthy', 'warning'] else 503
            return health_check, status_code
        
        # Add cache stats endpoint
        @app.route('/api/cache/stats')
        def cache_stats():
            """Cache statistics endpoint."""
            stats = app.cache.monitor.get_stats()
            top_keys = app.cache.monitor.get_top_keys()
            performance = app.cache.monitor.get_performance_metrics()
            
            return {
                'stats': stats,
                'top_keys': top_keys,
                'performance': performance
            }
        
        logger.info("Cache monitoring initialized successfully")