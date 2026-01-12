import os
import json
import redis
from typing import Optional, Any
from decimal import Decimal
from datetime import date, datetime

_redis_client = None

class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        if isinstance(obj, (date, datetime)):
            return obj.isoformat()
        return super().default(obj)

def get_redis_client():
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
    try:
        client = get_redis_client()
        if client:
            client.delete(key)
    except Exception as e:
        print(f"Cache delete error: {e}")

def get_cache_key_for_recommendation(username: str, query_hash: str) -> str:
    return f"recommendation:{username}:{query_hash}"

def get_cache_key_for_chat(username: str) -> str:
    return f"chat_history:{username}"

def get_cache_key_for_daily_nutrition(username: str, target_date: str) -> str:
    return f"nutrition:{username}:{target_date}"

def get_cache_key_for_7day_history(username: str) -> str:
    return f"history_7days:{username}"

def get_cache_key_for_logs(username: str, date_filter: str = None) -> str:
    if date_filter:
        return f"logs:{username}:{date_filter}"
    return f"logs:{username}:all"

def invalidate_nutrition_cache(username: str, affected_date: str = None):
    try:
        client = get_redis_client()
        if not client:
            return
        cache_delete(get_cache_key_for_7day_history(username))
        cache_delete(get_cache_key_for_logs(username))
        if affected_date:
            cache_delete(get_cache_key_for_logs(username, affected_date))

        if affected_date:
            cache_delete(get_cache_key_for_daily_nutrition(username, affected_date))
        else:
            from datetime import date, timedelta
            today = date.today()
            for i in range(7):
                target_date = today - timedelta(days=i)
                cache_delete(get_cache_key_for_daily_nutrition(username, str(target_date)))
    except Exception as e:
        print(f"Cache invalidation error: {e}")


