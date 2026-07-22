from datetime import datetime, timezone

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.agent.document.loader.document_loader import TxtLoader
from app.component.database.postgres_client import PostgresClient


async def splitter(docs: list[Document]):
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    all_splits = text_splitter.split_documents(docs)
    assert PostgresClient.vector_store is not None
    for split in all_splits:
        split.metadata["account_id"] = 12121212
        split.metadata["library_id"] = "lib_345678"
        split.metadata["document_id"] = "doc_789"
        split.metadata["chunk_index"] = 1  # 如果需要序号
        split.metadata["create_at"] = datetime.now(timezone.utc)
        split.metadata["update_at"] = datetime.now(timezone.utc)
    await PostgresClient.vector_store.aadd_documents(documents=all_splits)
    print(f"Split documentation into {len(all_splits)} chunks.")

