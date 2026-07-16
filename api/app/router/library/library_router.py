from fastapi import APIRouter, Depends

from app.request.library.library import LibraryDeleteRequest, LibraryRequest, LibraryUpdateRequest
from app.service.library.library_service import LibraryService, get_library_service

library_router = APIRouter(prefix="/library", tags=["library"])

@library_router.post("/create")
async def create_library(
    request: LibraryRequest,
    library_service: LibraryService = Depends(get_library_service),
):
    library_id = await library_service.create_library(request)
    return {"id": library_id}

@library_router.post("/delete")
async def delete_library(
    request: LibraryDeleteRequest,
    library_service: LibraryService = Depends(get_library_service),
):
    await library_service.delete_library(request)
    return {"status": "success"}

@library_router.post("/update")
async def update_library(
    request: LibraryUpdateRequest,
    library_service: LibraryService = Depends(get_library_service),
):
    return await library_service.update_library(request)

@library_router.get("/list")
async def get_library_list(
    library_service: LibraryService = Depends(get_library_service),
):
    return await library_service.get_library_list()

@library_router.post("/document/add")
async def add_document():
    pass

@library_router.post("/document/delete")
async def delete_document():
    pass

@library_router.post("/document/update")
async def update_document():
    pass

@library_router.get("/document/list")
async def get_document_list():
    pass

@library_router.post("/document/segment/add")
async def add_segment():
    pass

@library_router.post("/document/segment/delete")
async def delete_segment():
    pass

@library_router.post("/document/segment/update")
async def update_segment():
    pass

@library_router.get("/document/segment/list")
async def get_segment_list():
    pass
