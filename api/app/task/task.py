import asyncio

from celery import shared_task

from app.agent.document.manager.document_manager import DocumentManager
from app.agent.document.splitter.support.support_splitter import SupportSplitter
from app.component.database.postgres_client import PostgresClient
from app.repository.library.chunk_repository import ChunkRepository
from app.repository.library.document_repository import DocumentRepository
from app.repository.library.library_repository import LibraryRepository
from app.service.library.library_service import LibraryService

_loop: asyncio.AbstractEventLoop | None = None


def _get_loop() -> asyncio.AbstractEventLoop:
    global _loop
    if _loop is None or _loop.is_closed():
        _loop = asyncio.new_event_loop()
        asyncio.set_event_loop(_loop)
    assert _loop is not None
    return _loop


def _run_async(coro):
    return _get_loop().run_until_complete(coro)


async def _ensure_postgres() -> None:
    if PostgresClient.vector_store is None:
        await PostgresClient.initialize()


async def _process_document(
    document_id: str,
    account_id: int,
    splitter_type: str = SupportSplitter.DEFAULT.value,
    splitter_params: dict | None = None,
) -> dict:
    await _ensure_postgres()
    session_factory = PostgresClient.get_db()
    async with session_factory() as session:
        library_service = LibraryService(
            account_id=account_id,
            library_repository=LibraryRepository(session),
            document_repository=DocumentRepository(session),
            chunk_repository=ChunkRepository(session),
        )
        await library_service.get_document(document_id)
        manager = DocumentManager(library_service)
        splits = await manager.invoke(
            document_id,
            splitter_type=SupportSplitter(splitter_type),
            **(splitter_params or {}),
        )
        return {
            "document_id": document_id,
            "chunks": len(splits),
        }


@shared_task
def process_document_task(
    document_id: str,
    account_id: int,
    splitter_type: str = SupportSplitter.DEFAULT.value,
    splitter_params: dict | None = None,
) -> dict:
    """文档处理任务：加载 → 清洗 → 分割 → 写入 chunk_info / 向量库"""
    return _run_async(
        _process_document(
            document_id,
            account_id,
            splitter_type=splitter_type,
            splitter_params=splitter_params,
        )
    )
