import hashlib
from datetime import datetime, timezone
from enum import IntEnum

from langchain_core.documents import Document

from app.agent.document.cleaner import get_cleaner
from app.agent.document.loader import get_loader
from app.agent.document.splitter.document_splitter import DocumentSplitter
from app.agent.document.splitter.support.support_splitter import SupportSplitter
from app.component.database.postgres_client import PostgresClient
from app.request.library.library import (
    ChunkBatchAddRequest,
    ChunkItem,
    DocumentUpdateStatusRequest,
)
from app.service.file.file_service import FileService
from app.service.library.library_service import LibraryService


class DocumentStatus(IntEnum):
    """文档处理状态: 0 unprocess, 1 load, 2 clean, 3 split, 4 complete"""

    UNPROCESS = 0
    LOAD = 1
    CLEAN = 2
    SPLIT = 3
    COMPLETE = 4


class DocumentManager:
    """文档入库流水线：加载 → 清洗 → 分割 → 写入 chunk_info / 向量库"""

    def __init__(self, library_service: LibraryService):
        self.library_service = library_service

    async def _update_status(self, document_id: str, status: DocumentStatus) -> None:
        await self.library_service.update_document_status(
            DocumentUpdateStatusRequest(id=document_id, status=int(status))
        )

    @staticmethod
    def _content_hash(content: str) -> str:
        return hashlib.sha256(content.encode("utf-8")).hexdigest()

    async def invoke(
        self,
        document_id: str,
        splitter_type: SupportSplitter = SupportSplitter.DEFAULT,
        **kwargs,
    ) -> list[Document]:

        document_info = await self.library_service.get_document(document_id)
        file_ext = document_info.file_ext
        download_url = await FileService.get_direct_download_url(document_info.file_key)

        # 1. 加载
        loader = get_loader(file_ext)
        docs = loader.load(download_url)
        await self._update_status(document_id, DocumentStatus.LOAD)

        # 2. 清洗
        cleaner = get_cleaner(file_ext)
        cleaned_docs = cleaner.clean(docs)
        await self._update_status(document_id, DocumentStatus.CLEAN)
        if not cleaned_docs:
            return []

        # 3. 分割（kwargs 传给 splitter，如 chunk_size / chunk_overlap）
        splits = DocumentSplitter.split(
            cleaned_docs,
            splitter_type=splitter_type,
            **kwargs,
        )
        await self._update_status(document_id, DocumentStatus.SPLIT)
        if not splits:
            await self._update_status(document_id, DocumentStatus.COMPLETE)
            return []

        # 4. 写入 chunk_info
        chunk_ids = await self.library_service.batch_add_chunks(
            ChunkBatchAddRequest(
                document_id=document_id,
                chunks=[
                    ChunkItem(
                        position=index,
                        content=split.page_content,
                        hash=self._content_hash(split.page_content),
                    )
                    for index, split in enumerate(splits)
                ],
            )
        )

        # 5. 写入向量库所需 metadata
        now = datetime.now(timezone.utc)
        for index, (split, chunk_id) in enumerate(zip(splits, chunk_ids)):
            split.metadata["account_id"] = document_info.account_id
            split.metadata["library_id"] = document_info.library_id
            split.metadata["document_id"] = document_info.id
            split.metadata["chunk_id"] = chunk_id
            split.metadata["chunk_index"] = index
            split.metadata["create_at"] = now
            split.metadata["update_at"] = now

        assert PostgresClient.vector_store is not None
        await PostgresClient.vector_store.aadd_documents(documents=splits)
        await self._update_status(document_id, DocumentStatus.COMPLETE)
        return splits
