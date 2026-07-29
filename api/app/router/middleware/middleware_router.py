from fastapi import APIRouter, Depends

from app.request.middleware.middleware import (
    MiddlewareCreateRequest,
    MiddlewareDeleteRequest,
    MiddlewareUpdateRequest,
)
from app.service.middleware.middleware_service import (
    MiddlewareService,
    get_middleware_service,
)

middleware_router = APIRouter(prefix="/middleware", tags=["middleware"])


@middleware_router.post("/create")
async def create_middleware(
    request: MiddlewareCreateRequest,
    middleware_service: MiddlewareService = Depends(get_middleware_service),
):
    middleware_id = await middleware_service.create_middleware(request)
    return {"id": middleware_id}


@middleware_router.post("/delete")
async def delete_middleware(
    request: MiddlewareDeleteRequest,
    middleware_service: MiddlewareService = Depends(get_middleware_service),
):
    await middleware_service.delete_middleware(request)
    return {"status": "success"}


@middleware_router.post("/update")
async def update_middleware(
    request: MiddlewareUpdateRequest,
    middleware_service: MiddlewareService = Depends(get_middleware_service),
):
    return await middleware_service.update_middleware(request)


@middleware_router.get("/list")
async def get_middleware_list(
    middleware_service: MiddlewareService = Depends(get_middleware_service),
):
    return await middleware_service.get_middleware_list()
