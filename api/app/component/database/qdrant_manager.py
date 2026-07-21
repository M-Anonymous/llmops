import os

from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient
from app.agent.embedding.embedding import embeddings

class QdrantClientManager:

    _client: QdrantClient| None = None

    @classmethod
    def get_client(cls) -> QdrantClient:
        """
        获取 Qdrant 异步客户端单例
        """
        if cls._client is None:
            schema = os.getenv("QDRANT_SCHEMA","http")
            host = os.getenv("QDRANT_HOST", "llmops-qdrant")
            port = int(os.getenv("QDRANT_PORT", 6333))
            api_key = os.getenv("QDRANT_API_KEY", None)

            # 使用 gRPC 端口(6334)通常比 REST(6333)性能更好，
            # 但需确保 Docker 暴露了 6334 且客户端版本支持。
            # 这里为了兼容性默认使用 REST 端口，如需高性能可改为 6334 并设置 prefer_grpc=True
            cls._client = QdrantClient(
                url=f"{schema}://{host}:{port}",
                api_key=api_key,
                timeout=30,
                prefer_grpc=False
            )
        assert cls._client is not None
        return cls._client

    @classmethod
    async def close(cls):
        """优雅关闭连接"""
        if cls._client:
            cls._client.close()

qdrant_client = QdrantClientManager.get_client()

#vector_store = QdrantVectorStore(client=qdrant_client,collection_name="test",embedding=embeddings)
