import os

import psycopg
from langgraph.checkpoint.postgres import PostgresSaver
from langgraph.store.postgres import PostgresStore
from langgraph.store.postgres.base import PostgresIndexConfig
from psycopg.rows import dict_row
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.embedding.embedding import embeddings

class PostgresClient:

    _engine = None
    _async_session = None
    _pg_conn = None
    checkpointer = None
    store = None

    @classmethod
    def get_db_uri(cls) -> str:
        username = os.getenv("POSTGRES_USERNAME", "postgres")
        password = os.getenv("POSTGRES_PASSWORD", "")
        host = os.getenv("POSTGRES_HOST", "localhost")
        port = os.getenv("POSTGRES_PORT", "5432")
        dbname = os.getenv("POSTGRES_DATABASE", "postgres")
        return f"postgresql://{username}:{password}@{host}:{port}/{dbname}"

    @classmethod
    async def initialize(cls):
        """在 lifespan 事件中调用此函数，以初始化所有全局资源。"""
        # 1. 初始化数据库连接
        cls._pg_conn = psycopg.connect(
            cls.get_db_uri(),
            autocommit=True,          # 让 .setup() 能正确提交事务
            row_factory=dict_row)
        #短期记忆
        cls.checkpointer = PostgresSaver(cls._pg_conn)
        #长期记忆
        cls.store = PostgresStore(cls._pg_conn,
                                  index=PostgresIndexConfig(
                                      embed=embeddings,
                                      # 必须与模型的输出维度匹配
                                      dims=1024,
                                      distance_type="cosine",
                                  ))
        need_set_up = os.getenv("POSTGRES_NEED_SET_UP")
        if need_set_up:
            cls.checkpointer.setup()
            cls.store.setup()

    @classmethod
    async def cleanup(cls):
        if cls._pg_conn:
            cls._pg_conn.close()
            print("全局数据库连接已成功关闭。")

    @classmethod
    def get_db(cls) -> async_sessionmaker[AsyncSession]:
        # 单例模式：确保 Engine 和 SessionLocal 只被初始化一次
        if cls._engine is None:
            host = os.getenv("POSTGRES_HOST", "localhost")
            port = os.getenv("POSTGRES_PORT", "5432")
            username = os.getenv("POSTGRES_USERNAME", "postgres")
            password = os.getenv("POSTGRES_PASSWORD", "postgres")
            dbname = os.getenv("POSTGRES_DATABASE", "postgres")
            database_url = f"postgresql+asyncpg://{username}:{password}@{host}:{port}/{dbname}"
            cls._engine = create_async_engine(database_url)
            cls._async_session = async_sessionmaker(
                bind=cls._engine,
                class_=AsyncSession,
                expire_on_commit=False
            )
        return cls._async_session

    @classmethod
    async def close(cls):
        # 提供优雅关闭连接池的方法（可选，用于 FastAPI 的 lifespan 事件）
        if cls._engine:
            await cls._engine.dispose()

# FastAPI 依赖注入生成器
async def get_pg_session():
    pg_session = PostgresClient.get_db()
    async with pg_session() as session:
        try:
            yield session
        finally:
            # 确保异常情况下也能安全关闭 Session，归还连接池
            await session.close()

