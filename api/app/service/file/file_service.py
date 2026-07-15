import os
import uuid

from fastapi import UploadFile, HTTPException
from qcloud_cos import CosServiceError

from app.component import CosClient


class FileService:
    """基于腾讯云 COS 的文件业务服务"""

    @classmethod
    async def upload_file(cls, file: UploadFile, folder: str = "uploads") -> dict:
        """上传文件到 COS"""
        try:
            # 1. 直接获取现有的单例客户端
            client = CosClient.get_cos_client()
            bucket = CosClient.get_bucket_name()

            if file.filename is None:
                raise HTTPException(status_code=400, detail="Uploaded file must have a filename")
            # 2. 生成唯一文件名，防止覆盖
            file_ext = os.path.splitext(file.filename)[1]
            unique_filename = f"{folder}/{uuid.uuid4().hex}{file_ext}"

            # 3. 读取文件内容
            content = await file.read()

            # 4. 上传到 COS
            response = client.put_object(
                Bucket=bucket,
                Body=content,
                Key=unique_filename,
                ContentType=file.content_type or "application/octet-stream"
            )

            return {
                "status": "success",
                "filename": file.filename,
                "cos_key": unique_filename,
                "etag": response.get("ETag", "").strip('"'),
                "size": len(content)
            }

        except CosServiceError as e:
            raise HTTPException(status_code=500, detail=f"COS upload failed: {e.get_error_msg()}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"File upload failed: {str(e)}")

    @classmethod
    async def download_file(cls, cos_key: str) -> bytes:
        """从 COS 下载文件"""
        try:
            client = CosClient.get_cos_client()
            bucket = CosClient.get_bucket_name()

            response = client.get_object(Bucket=bucket, Key=cos_key)
            return response["Body"].get_raw_stream().read()

        except CosServiceError as e:
            if e.get_error_code() == "NoSuchKey":
                raise HTTPException(status_code=404, detail="File not found")
            raise HTTPException(status_code=500, detail=f"COS download failed: {e.get_error_msg()}")

    @classmethod
    async def delete_file(cls, cos_key: str) -> dict:
        """从 COS 删除文件"""
        try:
            client = CosClient.get_cos_client()
            bucket = CosClient.get_bucket_name()

            client.delete_object(Bucket=bucket, Key=cos_key)
            return {"status": "success", "message": f"File {cos_key} deleted"}

        except CosServiceError as e:
            raise HTTPException(status_code=500, detail=f"COS delete failed: {e.get_error_msg()}")