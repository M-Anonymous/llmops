import os
from qdrant_client import AsyncQdrantClient

class QdrantClientManager:
    _client: AsyncQdrantClient | None = None

    @classmethod
    def get_client(cls) -> AsyncQdrantClient | None:
        """
        获取 Qdrant 异步客户端单例
        """
        if cls._client is None:
            host = os.getenv("QDRANT_HOST", "llmops-qdrant")
            port = int(os.getenv("QDRANT_PORT", 6333))
            api_key = os.getenv("QDRANT_API_KEY", None)

            # 使用 gRPC 端口(6334)通常比 REST(6333)性能更好，
            # 但需确保 Docker 暴露了 6334 且客户端版本支持。
            # 这里为了兼容性默认使用 REST 端口，如需高性能可改为 6334 并设置 prefer_grpc=True
            cls._client = AsyncQdrantClient(
                url=f"https://{host}:{port}",
                api_key=api_key,
                timeout=30,
                prefer_grpc=False
            )
        return cls._client

    @classmethod
    async def close(cls):
        """优雅关闭连接"""
        if cls._client:
            await cls._client.close()
            cls._client = None

async def get_qdrant_client() -> AsyncQdrantClient | None:
    """
    在路由中通过 Depends(get_qdrant_client) 使用
    """
    return QdrantClientManager.get_client()