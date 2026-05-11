import redis.asyncio as redis
from app.core.config import settings


redis_client = redis.from_url(url=settings.REDIS_URI, decode_responses=True)


async def get_redis_client():
    return redis_client