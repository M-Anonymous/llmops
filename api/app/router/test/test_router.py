from fastapi import APIRouter

from app.agent.document.loader.document_loader import TxtLoader
from app.agent.document.parser.document_splitter import splitter
from app.component.database.postgres_client import PostgresClient

test_router = APIRouter(prefix="/test")


@test_router.get("/store")
async def test_store(url : str):
    loader = TxtLoader()
    documents = loader.load(url)
    await splitter(documents)


@test_router.get("/search")
async def test_search(question : str):
    assert PostgresClient.vector_store is not None
    results = await PostgresClient.vector_store.asimilarity_search_with_score(
    question,
    k=10)
    return results