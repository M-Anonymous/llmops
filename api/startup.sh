#!/bin/bash

# 1. 启用错误检查
set -e

# 2. 检测运行的模式(api/celery)，以执行不同的脚本
if [[ "${MODE}" == "celery" ]]; then
  # 4. 运行 Celery 命令
  celery -A "${CELERY_APP_PATH:-app.component.worker.celery_client.celery}" worker \
    -P "${CELERY_WORKER_CLASS:-prefork}" \
    -c "${CELERY_WORKER_AMOUNT:-5}" \
    --loglevel INFO
else
  uvicorn main:app \
      --host 0.0.0.0 \
      --port 8888 \
      --reload
fi