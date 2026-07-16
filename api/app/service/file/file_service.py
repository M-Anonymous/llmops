import os
import re
import uuid

from fastapi import HTTPException
from app.component import CosClient

# 允许上传的文件后缀与 Content-Type 映射
ALLOWED_EXTENSIONS: dict[str, str] = {
    ".pdf": "application/pdf",
    ".doc": "application/msword",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ".txt": "text/plain",
    ".md": "text/markdown",
}


class FileService:
    """基于腾讯云 COS 的文件业务服务"""

    @classmethod
    async def get_presigned_upload_url(
        cls,
        filename: str,
        extension: str,
        folder: str = "uploads",
    ) -> dict:
        """生成 COS PUT 预签名上传 URL，限制文件格式"""
        safe_filename = cls._validate_filename(filename)
        ext, content_type = cls._resolve_extension(extension)
        expire_seconds = int(os.getenv("COS_PRESIGNED_EXPIRE", "900"))

        client = CosClient.get_cos_client()
        bucket = CosClient.get_bucket_name()
        if not bucket:
            raise HTTPException(status_code=500, detail="COS 配置不完整")

        cos_key = cls._build_cos_key(folder, safe_filename, ext)
        upload_url = client.get_presigned_url(
            Bucket=bucket,
            Key=cos_key,
            Method="POST",
            Expired=expire_seconds,
            Headers={"Content-Type": content_type},
        )

        return {
            "upload_url": upload_url,
            "cos_key": cos_key,
            "filename": f"{safe_filename}{ext}",
            "content_type": content_type,
            "expire_seconds": expire_seconds,
        }

    @classmethod
    async def get_presigned_download_url(cls, cos_key: str) -> dict:
        """生成 COS 预签名下载 URL"""
        key = cls._validate_cos_key(cos_key)
        expire_seconds = int(os.getenv("COS_PRESIGNED_EXPIRE", "900"))

        client = CosClient.get_cos_client()
        bucket = CosClient.get_bucket_name()
        if not bucket:
            raise HTTPException(status_code=500, detail="COS 配置不完整")

        download_url = client.get_presigned_download_url(
            Bucket=bucket,
            Key=key,
            Expired=expire_seconds,
        )

        return {
            "download_url": download_url,
            "cos_key": key,
            "expire_seconds": expire_seconds,
        }

    @staticmethod
    def _normalize_extension(extension: str) -> str:
        ext = extension.strip().lower()
        if not ext.startswith("."):
            ext = f".{ext}"
        return ext

    @staticmethod
    def _validate_filename(filename: str) -> str:
        safe_name = os.path.basename(filename.strip())
        if not safe_name:
            raise HTTPException(status_code=400, detail="文件名不能为空")
        if safe_name in {".", ".."} or re.search(r'[\\/:*?"<>|]', safe_name):
            raise HTTPException(status_code=400, detail="文件名包含非法字符")
        return safe_name

    @classmethod
    def _resolve_extension(cls, extension: str) -> tuple[str, str]:
        ext = cls._normalize_extension(extension)
        content_type = ALLOWED_EXTENSIONS.get(ext)
        if not content_type:
            allowed = ", ".join(sorted(ALLOWED_EXTENSIONS.keys()))
            raise HTTPException(
                status_code=400,
                detail=f"不支持的文件格式: {ext}，允许格式: {allowed}",
            )
        return ext, content_type

    @classmethod
    def _build_cos_key(cls, folder: str, filename: str, extension: str) -> str:
        folder = folder.strip("/")
        return f"{folder}/{uuid.uuid4().hex}_{filename}{extension}"

    @classmethod
    def _validate_cos_key(cls, cos_key: str) -> str:
        key = cos_key.strip()
        if not key:
            raise HTTPException(status_code=400, detail="cos_key 不能为空")
        if key.startswith("/") or ".." in key:
            raise HTTPException(status_code=400, detail="cos_key 不合法")
        return key