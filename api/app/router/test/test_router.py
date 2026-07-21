from fastapi import APIRouter

test_router = APIRouter(prefix="/test")


@test_router.get("/store")
async def test_store():
    return ""
