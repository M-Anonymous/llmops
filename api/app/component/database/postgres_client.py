import os
from typing import Optional
from psycopg_pool import AsyncConnectionPool
from langchain_postgres import PGEngine, PGVectorStore
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langgraph.store.postgres.aio import AsyncPostgresStore
from langgraph.store.postgres.base import PostgresIndexConfig
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from app.agent.embedding.embedding import embeddings


class PostgresClient:
    # 使用类型注解明确变量类型
    _pool: Optional[AsyncConnectionPool] = None
    _engine = None
    _async_session_maker: Optional[async_sessionmaker[AsyncSession]] = None

    checkpointer: Optional[AsyncPostgresSaver] = None
    store: Optional[AsyncPostgresStore] = None
    vector_store: Optional[PGVectorStore] = None

    @classmethod
    def get_db_address(cls) -> str:
        """获取标准的数据库连接字符串（无驱动前缀）"""
        username = os.getenv("POSTGRES_USERNAME", "postgres")
        password = os.getenv("POSTGRES_PASSWORD", "")
        host = os.getenv("POSTGRES_HOST", "localhost")
        port = os.getenv("POSTGRES_PORT", "5432")
        dbname = os.getenv("POSTGRES_DATABASE", "postgres")
        return f"{username}:{password}@{host}:{port}/{dbname}"

    @classmethod
    async def initialize(cls):
        """在应用启动时异步初始化所有全局资源。"""
        db_address = cls.get_db_address()

        # --- 1. 创建用于 checkpointer 和 store 的连接池 ---
        # 注意：AsyncPostgresSaver 和 AsyncPostgresStore 需要异步连接池
        cls._pool =  AsyncConnectionPool(
            "postgresql://"+db_address,
            min_size=1,
            max_size=5,
            kwargs={"autocommit": True, "prepare_threshold": 0}  # 重要：LangGraph 需要 autocommit
        )
        if cls._pool is None:
            raise RuntimeError("Connection pool is not initialized.")

        print("✅ 异步连接池已创建。")
        await cls._pool.open()

        # --- 2. 初始化 Checkpointer (短期记忆) ---
        # 使用异步版本的 Saver，并传入连接池
        cls.checkpointer = AsyncPostgresSaver(cls._pool)
        print("✅ 短期记忆 (Checkpointer) 准备就绪。")

        # --- 3. 初始化 Store (长期记忆) ---
        cls.store = AsyncPostgresStore(
            cls._pool,
            index=PostgresIndexConfig(
                embed=embeddings,
                dims=1024,  # 请确认你的向量维度
                distance_type="cosine",
            )
        )
        print("✅ 长期记忆 (Store) 准备就绪。")

        # --- 4. 初始化 VectorStore (向量数据库) ---
        # 创建异步 PGEngine
        pg_engine = PGEngine.from_connection_string(
            url="postgresql+asyncpg://"+db_address,  # 这里不需要加驱动前缀，PGEngine 内部会处理
            pool_size=5,
        )
        # 使用异步方法创建 VectorStore
        cls.vector_store = await PGVectorStore.create(
            engine=pg_engine,
            table_name='vector_store',  # 建议使用有意义的表名
            id_column='id',
            embedding_service=embeddings,
        )
        print("✅ 向量存储 (VectorStore) 准备就绪。")
        # --- 5. 执行数据库表初始化 (仅首次启动) ---
        assert cls.checkpointer is not None
        assert cls.store is not None
        need_set_up = os.getenv("POSTGRES_NEED_SET_UP", "false").lower() == "true"
        if need_set_up:
            print("🔧 正在执行数据库表初始化 (setup)...")
            # 注意：这些 setup 方法本身是异步的
            await cls.checkpointer.setup()
            await cls.store.setup()
            # VectorStore 会自动创建表，通常不需要手动 setup
            # 但如果你需要创建集合，可以在这里添加逻辑
            print("✅ 数据库表初始化完成。")

    @classmethod
    async def cleanup(cls):
        """在应用关闭时优雅地释放所有资源。"""
        if cls._pool:
            await cls._pool.close()
            print("✅ 数据库连接池已关闭。")

        if cls._engine:
            await cls._engine.dispose()
            print("✅ SQLAlchemy 引擎已释放。")

    @classmethod
    def get_db(cls) -> async_sessionmaker[AsyncSession]:
        """获取用于 SQLAlchemy ORM 的异步会话工厂。"""
        if cls._async_session_maker is None:
            # 复用相同的连接字符串，加上 asyncpg 驱动用于 ORM
            async_db_uri = "postgresql+asyncpg://" + cls.get_db_address()
            cls._engine = create_async_engine(async_db_uri, echo=False)
            cls._async_session_maker = async_sessionmaker(
                bind=cls._engine,
                class_=AsyncSession,
                expire_on_commit=False
            )
        assert cls._async_session_maker is not None
        return cls._async_session_maker


# --- FastAPI 依赖注入 ---
async def get_pg_session():
    """用于 FastAPI 依赖项的异步会话生成器。"""
    session_factory = PostgresClient.get_db()
    async with session_factory() as session:
        try:
            yield session
        finally:
            await session.close()