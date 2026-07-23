from fastapi import APIRouter, Depends

from app.agent.document.manager.document_manager import DocumentManager
from app.agent.document.splitter.document_splitter import resolve_splitter_type
from app.component.database.postgres_client import PostgresClient
from app.service.library.library_service import LibraryService, get_library_service

test_router = APIRouter(prefix="/test")


@test_router.get("/store")
async def test_store(
    document_id: str,
    library_service: LibraryService = Depends(get_library_service),
):
    document = await library_service.get_document(document_id)
    manager = DocumentManager(library_service)
    splits = await manager.invoke(
        document_id,
        splitter_type=resolve_splitter_type(document.file_ext),
    )
    return {"chunks": len(splits), "document_id": document.id}


@test_router.get("/search")
async def test_search(question: str):
    assert PostgresClient.vector_store is not None
    results = await PostgresClient.vector_store.asimilarity_search_with_score(
        question,
        k=10,
    )
    return results
