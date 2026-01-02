import os
from celery import Celery

redis_host = os.getenv('REDIS_HOST', 'localhost')
redis_port = int(os.getenv('REDIS_PORT', 6379))
redis_password = os.getenv('REDIS_PASSWORD', None)
redis_db = int(os.getenv('REDIS_DB', 0))

redis_url = f"redis://"
if redis_password:
    redis_url = f"redis://:{redis_password}@"
redis_url += f"{redis_host}:{redis_port}/{redis_db}"

celery_app = Celery(
    'nutrition_app',
    broker=redis_url,
    backend=redis_url
)

celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=300,
    task_soft_time_limit=240,
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=50
)

@celery_app.task(bind=True, max_retries=3)
def process_llm_message(self, api_key: str, messages: list, tools: list, username: str, llm_provider: str):
    """Background task to process LLM message."""
    try:
        from chat_handler import call_anthropic_api, call_openai_api
        from redis_client import cache_set, get_cache_key_for_recommendation
        import hashlib

        result = call_anthropic_api(api_key, messages, tools, username)
        
        # Cache successful results
        if "error" not in result:
            user_message = messages[-1].get("content", "") if messages else ""
            query_hash = hashlib.md5(user_message.strip().lower().encode()).hexdigest()
            cache_key = get_cache_key_for_recommendation(username, query_hash)
            cache_set(cache_key, result, ttl=3600)
        return result

    except Exception as e:
        print(f"LLM task error (attempt {self.request.retries + 1}): {e}")
        import traceback
        traceback.print_exc()
        if self.request.retries < self.max_retries:
            raise self.retry(exc=e, countdown=2 ** self.request.retries)
        return {"error": f"LLM processing failed after retries: {str(e)}"}

