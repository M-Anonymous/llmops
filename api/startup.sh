#!/bin/bash

# 1. 启用错误检查
set -e

# 2. 判断是否启用了数据库迁移（FastAPI 通常搭配 Alembic 进行迁移）
if [[ "${MIGRATION_ENABLED}" == "true" ]]; then
  echo "Runnable migrations"
  # 注意：这里假设你使用的是 alembic，如果你的迁移脚本有自定义名称请自行修改
  alembic upgrade head
fi

# 3. 检测运行的模式(api/celery)，以执行不同的脚本
if [[ "${MODE}" == "celery" ]]; then
  # 4. 运行 Celery 命令
  celery -A "${CELERY_APP_PATH:-app.component.worker.celery_client.celery}" worker \
    -P "${CELERY_WORKER_CLASS:-prefork}" \
    -c "${CELERY_WORKER_AMOUNT:-5}" \
    --loglevel INFO
else
  uvicorn app.main:app \
      --host 0.0.0.0 \
      --port 8888 \
      --reload
fi