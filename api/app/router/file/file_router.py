from fastapi import APIRouter, File, UploadFile, HTTPException

from app.request.file.file import PresignedDownloadRequest, PresignedUploadRequest
from app.service.file.file_service import FileService

file_router = APIRouter(prefix="/file", tags=["file"])


@file_router.post("/presigned_upload")
async def get_presigned_upload_url(request: PresignedUploadRequest):
    return await FileService.get_presigned_upload_url(
        filename=request.filename,
        extension=request.extension,
        folder=request.folder or "uploads",
    )


@file_router.post("/presigned_download")
async def get_presigned_download_url(request: PresignedDownloadRequest):
    return await FileService.get_presigned_download_url(request.cos_key)
