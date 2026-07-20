from fastapi import APIRouter

from app.component.database.postgres_client import PostgresClient

test_router = APIRouter(prefix="/test", tags=["tool"])


@test_router.get("/store")
async def test_store():
    store = PostgresClient.store
    return store.put(
        (
            "users",
        ),  # Namespace to group related data together (users namespace for user data)
        "user_123",  # Key within the namespace (user ID as key)
        {
            "name": "John Smith",
            "language": "English",
        },  # Data to store for the given user
    )
