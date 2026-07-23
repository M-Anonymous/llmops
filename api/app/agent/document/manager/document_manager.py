from datetime import datetime, timezone

from langchain_core.documents import Document

from app.agent.document.cleaner import get_cleaner
from app.agent.document.loader import get_loader
from app.agent.document.splitter.document_splitter import DocumentSplitter
from app.agent.document.splitter.support.support_splitter import SupportSplitter
from app.component.database.postgres_client import PostgresClient
from app.service.file.file_service import FileService
from app.service.library.library_service import LibraryService


class DocumentManager:
    """文档入库流水线：加载 → 清洗 → 分割 → 写入向量库"""

    def __init__(self, library_service: LibraryService):
        self.library_service = library_service

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

        # 2. 清洗
        cleaner = get_cleaner(file_ext)
        cleaned_docs = cleaner.clean(docs)
        if not cleaned_docs:
            return []

        # 3. 分割（kwargs 传给 splitter，如 chunk_size / chunk_overlap）
        splits = DocumentSplitter.split(
            cleaned_docs,
            splitter_type=splitter_type,
            **kwargs,
        )

        # 4. 写入向量库所需 metadata
        now = datetime.now(timezone.utc)
        for index, split in enumerate(splits):
            split.metadata["account_id"] = document_info.account_id
            split.metadata["library_id"] = document_info.library_id
            split.metadata["document_id"] = document_info.id
            split.metadata["chunk_index"] = index
            split.metadata["create_at"] = now
            split.metadata["update_at"] = now

        assert PostgresClient.vector_store is not None
        await PostgresClient.vector_store.aadd_documents(documents=splits)
        return splits
