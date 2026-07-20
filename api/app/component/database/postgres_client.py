import os
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession


class PostgresClient:

    _engine = None
    _async_session = None

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

def get_db_uri() -> str:
    username = os.getenv("POSTGRES_USERNAME", "postgres")
    password = os.getenv("POSTGRES_PASSWORD", "")
    host = os.getenv("POSTGRES_HOST", "localhost")
    port = os.getenv("POSTGRES_PORT", "5432")
    dbname = os.getenv("POSTGRES_DATABASE", "postgres")
    return f"postgresql://{username}:{password}@{host}:{port}/{dbname}"