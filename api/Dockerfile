# syntax=docker/dockerfile:1
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim AS builder
WORKDIR /llmops/api
COPY pyproject.toml uv.lock ./
# 挂载 uv 的缓存目录，避免每次构建都重新下载依赖
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-install-project
COPY . .
# 5. 再次 sync 以安装项目本身
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen

FROM python:3.12-slim AS production
WORKDIR /llmops/api
COPY --from=builder /llmops/api/.venv ./.venv
COPY .env main.py startup.sh ./
COPY ./app /llmops/api/app/
# 配置环境变量，将虚拟环境的 bin 目录添加到 PATH 前面
ENV PATH="/llmops/api/.venv/bin:$PATH"

RUN chmod +x startup.sh

ENTRYPOINT ["/bin/bash", "/llmops/api/startup.sh"]
