from fastapi import APIRouter, Depends, Query

from app.request.library.library import (
    ChunkAddRequest,
    ChunkBatchAddRequest,
    ChunkDeleteRequest,
    ChunkUpdateRequest,
    DocumentAddRequest,
    DocumentDeleteRequest,
    DocumentDownloadRequest,
    DocumentParseRequest,
    DocumentUpdateStatusRequest,
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

@library_router.post("/document/update")
async def update_document_status(
    request: DocumentUpdateStatusRequest,
    library_service: LibraryService = Depends(get_library_service),
):
    return await library_service.update_document_status(request)

@library_router.post("/document/download")
async def download_document(
    request: DocumentDownloadRequest,
    library_service: LibraryService = Depends(get_library_service),
):
    return await library_service.download_document(request)

@library_router.post("/document/parse")
async def parse_document(
    request: DocumentParseRequest,
    library_service: LibraryService = Depends(get_library_service),
):
    return await library_service.parse_document(request)

@library_router.get("/document/list")
async def get_document_list(
    library_id: str = Query(..., description="知识库ID"),
    library_service: LibraryService = Depends(get_library_service),
):
    return await library_service.get_document_list(library_id)

@library_router.post("/document/chunk/add")
async def add_chunk(
    request: ChunkAddRequest,
    library_service: LibraryService = Depends(get_library_service),
):
    chunk_id = await library_service.add_chunk(request)
    return {"id": chunk_id}

@library_router.post("/document/chunk/batch-add")
async def batch_add_chunks(
    request: ChunkBatchAddRequest,
    library_service: LibraryService = Depends(get_library_service),
):
    chunk_ids = await library_service.batch_add_chunks(request)
    return {"ids": chunk_ids}

@library_router.post("/document/chunk/delete")
async def delete_chunk(
    request: ChunkDeleteRequest,
    library_service: LibraryService = Depends(get_library_service),
):
    await library_service.delete_chunk(request)
    return {"status": "success"}

@library_router.post("/document/chunk/update")
async def update_chunk(
    request: ChunkUpdateRequest,
    library_service: LibraryService = Depends(get_library_service),
):
    return await library_service.update_chunk(request)

@library_router.get("/document/chunk/list")
async def get_chunk_list(
    document_id: str = Query(..., description="文档ID"),
    library_service: LibraryService = Depends(get_library_service),
):
    return await library_service.get_chunk_list(document_id)
