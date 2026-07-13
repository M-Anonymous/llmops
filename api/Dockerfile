# syntax=docker/dockerfile:1
FROM python:3.12-slim as base
RUN pip install uv
COPY pyproject.toml .
# 挂载 uv 的缓存目录，避免每次构建都重新下载依赖
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --production


FROM base as production
WORKDIR /app/api
COPY .env main.py startup.sh ./app ./
RUN chmod +x startup.sh

EXPOSE 8888

ENTRYPOINT ["/bin/bash", "/startup.sh"]
