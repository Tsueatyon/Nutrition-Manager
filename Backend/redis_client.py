import os
import json
import redis
from typing import Optional, Any
from decimal import Decimal
from datetime import date, datetime

_redis_client = None

class CustomJSONEncoder(json.JSONEncoder):
    """Custom JSON encoder to handle Decimal, date, and datetime objects."""
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        if isinstance(obj, (date, datetime)):
            return obj.isoformat()
        return super().default(obj)

def get_redis_client():
    """Get or create Redis client. Works with GCloud Memorystore or local Redis."""
    global _redis_client
    
    if _redis_client is not None:
        return _redis_client
    
    redis_host = os.getenv('REDIS_HOST', 'localhost')
    redis_port = int(os.getenv('REDIS_PORT', 6379))
    redis_password = os.getenv('REDIS_PASSWORD', None)
    redis_db = int(os.getenv('REDIS_DB', 0))
    
    try:
        _redis_client = redis.Redis(
            host=redis_host,
            port=redis_port,
            password=redis_password,
            db=redis_db,
            decode_responses=True,
            socket_connect_timeout=5,
            socket_timeout=5,
            health_check_interval=30
        )
        _redis_client.ping()
        print(f"Redis connected: {redis_host}:{redis_port}")
        return _redis_client
    except Exception as e:
        print(f"Redis connection failed: {e}. Continuing without cache.")
        return None

def cache_get(key: str) -> Optional[Any]:
    """Get value from cache."""
    try:
        client = get_redis_client()
        if not client:
            return None
        
        value = client.get(key)
        if value:
            return json.loads(value)
        return None
    except Exception as e:
        print(f"Cache get error: {e}")
        return None

def cache_set(key: str, value: Any, ttl: int = 3600):
    """Set value in cache with TTL (default 1 hour)."""
    try:
        client = get_redis_client()
        if not client:
            return False
        
        client.setex(key, ttl, json.dumps(value, cls=CustomJSONEncoder))
        return True
    except Exception as e:
        print(f"Cache set error: {e}")
        return False

def cache_delete(key: str):
    """Delete key from cache."""
    try:
        client = get_redis_client()
        if client:
            client.delete(key)
    except Exception as e:
        print(f"Cache delete error: {e}")

def get_cache_key_for_recommendation(username: str, query_hash: str) -> str:
    """Generate cache key for recommendation."""
    return f"recommendation:{username}:{query_hash}"

def get_cache_key_for_chat(username: str) -> str:
    """Generate cache key for chat history."""
    return f"chat_history:{username}"

def get_cache_key_for_daily_nutrition(username: str, target_date: str) -> str:
    """Generate cache key for daily nutrition data."""
    return f"nutrition:{username}:{target_date}"

def get_cache_key_for_7day_history(username: str) -> str:
    """Generate cache key for 7-day nutrition history."""
    return f"history_7days:{username}"

def get_cache_key_for_logs(username: str, date_filter: str = None) -> str:
    """Generate cache key for food intake logs."""
    if date_filter:
        return f"logs:{username}:{date_filter}"
    return f"logs:{username}:all"

def invalidate_nutrition_cache(username: str, affected_date: str = None):
    """Invalidate all nutrition-related cache for a user.
    If affected_date is provided, only invalidates cache for that date and 7-day history.
    Otherwise, invalidates all nutrition cache for the user.
    """
    try:
        client = get_redis_client()
        if not client:
            return
        
        # Always invalidate 7-day history cache
        cache_delete(get_cache_key_for_7day_history(username))
        
        # Invalidate logs cache (all variations)
        cache_delete(get_cache_key_for_logs(username))
        cache_delete(get_cache_key_for_logs(username, "all"))
        if affected_date:
            cache_delete(get_cache_key_for_logs(username, affected_date))
        
        # Invalidate daily nutrition cache
        if affected_date:
            cache_delete(get_cache_key_for_daily_nutrition(username, affected_date))
        else:
            # If no specific date, invalidate all dates in past 7 days
            from datetime import date, timedelta
            today = date.today()
            for i in range(7):
                target_date = today - timedelta(days=i)
                cache_delete(get_cache_key_for_daily_nutrition(username, str(target_date)))
    except Exception as e:
        print(f"Cache invalidation error: {e}")


