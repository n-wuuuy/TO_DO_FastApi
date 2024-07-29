import time

from fastapi import FastAPI

from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend
from fastapi_cache.decorator import cache

from src.config import REDIS_HOST, REDIS_PORT
from src.tasks.router import router as router_tasks
from src.user.router import router as user_router
from src.celery_task.router import router as celery_router

from redis import asyncio as aioredis

app = FastAPI()

app.include_router(router_tasks)
app.include_router(user_router)
app.include_router(celery_router)


@cache()
async def get_cache():
    return 1


@app.get("/")
@cache(expire=60)
async def index():
    time.sleep(5)
    return dict(hello="world")


@app.on_event("startup")
async def startup():
    redis = aioredis.from_url(f"redis://{REDIS_HOST}:{REDIS_PORT}")
    FastAPICache.init(RedisBackend(redis), prefix="fastapi-cache")