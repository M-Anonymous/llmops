from fastapi import APIRouter, Depends, Query

from app.request.library.library import (
    DocumentAddRequest,
    DocumentDeleteRequest,
    DocumentDownloadRequest,
    LibraryDeleteRequest,
    LibraryRequest,
    LibraryUpdateRequest,
)
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
async def add_document(
    request: DocumentAddRequest,
    library_service: LibraryService = Depends(get_library_service),
):
    document_id = await library_service.add_document(request)
    return {"id": document_id}

@library_router.post("/document/delete")
async def delete_document(
    request: DocumentDeleteRequest,
    library_service: LibraryService = Depends(get_library_service),
):
    await library_service.delete_document(request)
    return {"status": "success"}

@library_router.post("/document/download")
async def download_document(
    request: DocumentDownloadRequest,
    library_service: LibraryService = Depends(get_library_service),
):
    return await library_service.download_document(request)

@library_router.get("/document/list")
async def get_document_list(
    library_id: str = Query(..., description="知识库ID"),
    library_service: LibraryService = Depends(get_library_service),
):
    return await library_service.get_document_list(library_id)

@library_router.post("/document/chunk/add")
async def add_chunk():
    pass

@library_router.post("/document/chunk/delete")
async def delete_chunk():
    pass

@library_router.post("/document/chunk/update")
async def update_chunk():
    pass

@library_router.get("/document/chunk/list")
async def get_chunk_list():
    pass
