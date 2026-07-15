import os
import redis.asyncio as redis  # 1. 统一使用异步模块
from redis.asyncio.connection import Connection, SSLConnection


class RedisAsyncClient:
    _redis_async_client = None

    @classmethod
    def get_redis_client(cls) -> redis.Redis:
        if cls._redis_async_client is None:
            connection_class = Connection
            # 2. 环境变量判断更严谨
            if os.getenv("REDIS_USE_SSL", "").lower() == "true":
                connection_class = SSLConnection

            redis_pool = redis.ConnectionPool(
                host=os.getenv("REDIS_HOST", "localhost"),
                port=int(os.getenv("REDIS_PORT", 6379)),  # 3. 显式转为整数
                username=os.getenv("REDIS_USERNAME", None),
                password=os.getenv("REDIS_PASSWORD", None),
                db=int(os.getenv("REDIS_DB", 0)),  # 3. 显式转为整数
                encoding="utf-8",
                connection_class=connection_class
            )
            cls._redis_async_client = redis.Redis(connection_pool=redis_pool)

        return cls._redis_async_client

redis_async_client = RedisAsyncClient.get_redis_client()