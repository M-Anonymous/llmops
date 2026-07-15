import os
import uuid

from fastapi import APIRouter, File, UploadFile, HTTPException

from app.component.cos.cos_client import cos_client

file_router = APIRouter(prefix="/file")


@file_router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    try:
        # 生成唯一文件名，防止覆盖
        if not file.filename:
            raise HTTPException(status_code=400, detail="未提供有效的文件名")
        file_extension = os.path.splitext(file.filename)[-1]
        unique_filename = f"{uuid.uuid4().hex}{file_extension}"
        cos_key = f"uploads/{unique_filename}"
        content = await file.read()
        cos_client.put_object(
            Bucket=cos_client.get_bucket_name(),
            Body=content,
            Key=cos_key,
            EnableMD5=False
        )
        return {
            "code": 200,
            "message": "上传成功",
            "data": {
                "cos_key": cos_key,
                "original_filename": file.filename
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"上传失败: {str(e)}")