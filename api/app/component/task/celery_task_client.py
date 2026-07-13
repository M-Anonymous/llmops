import os
from celery import Celery
from celery.result import AsyncResult


class CeleryClient:
    _celery_app = None

    @classmethod
    def get_celery_app(cls) -> Celery:
        # 单例模式：确保 Celery 实例只被初始化一次
        if cls._celery_app is None:
            # 1. 从环境变量读取并拼接 URL
            redis_host = os.getenv("REDIS_HOST", "localhost")
            redis_port = os.getenv("REDIS_PORT", "6379")
            broker_db = os.getenv("CELERY_BROKER_DB", "1")
            result_db = os.getenv("CELERY_RESULT_BACKEND_DB", "2")  # 建议 Broker 和 Backend 用不同的 DB

            broker_url = f"redis://{redis_host}:{redis_port}/{broker_db}"
            result_backend_url = f"redis://{redis_host}:{redis_port}/{result_db}"

            # 2. 安全处理布尔值环境变量（防止 "False" 字符串变成 True）
            ignore_result = os.getenv("CELERY_TASK_IGNORE_RESULT", "False").lower() == "true"
            result_expires = int(os.getenv("CELERY_RESULT_EXPIRES", "3600"))

            # 3. 创建 Celery 实例并直接传入配置
            cls._celery_app = Celery(
                "worker",
                broker=broker_url,
                backend=result_backend_url,
                # 将其他配置以字典形式传入
                config_overrides={
                    "task_ignore_result": ignore_result,
                    "result_expires": result_expires,
                    "broker_connection_retry_on_startup": True,  # 启动时重试连接，生产环境建议直接写死 True
                    "task_track_started": True,  # 追踪任务开始状态
                }
            )

        return cls._celery_app


    # FastAPI 依赖注入生成器：用于在路由中获取任务状态
    @classmethod
    async def get_task_result(cls,task_id: str):
        result = AsyncResult(task_id, app=cls.get_celery_app())
        return {
            "task_id": task_id,
            "status": result.status,
            "result": result.result if result.ready() else None
        }