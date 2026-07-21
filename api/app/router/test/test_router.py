from fastapi import APIRouter

from app.agent.document.loader.document_loader import loader
from app.component.database.postgres_client import PostgresClient

test_router = APIRouter(prefix="/test", tags=["tool"])


@test_router.get("/store")
async def test_store():
    document = loader.load()
    return document
