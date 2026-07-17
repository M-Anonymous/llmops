from typing import Optional

from pydantic import BaseModel, Field


class PresignedUploadRequest(BaseModel):
    """获取 COS 预签名上传参数"""

    filename: str = Field(..., max_length=255, description="文件名（不含后缀）")
    extension: str = Field(..., max_length=20, description="文件后缀，如 pdf、.pdf")
    folder: Optional[str] = Field(default="uploads", max_length=100, description="COS 存储目录")


class PresignedDownloadRequest(BaseModel):
    """获取 COS 预签名下载 URL"""

    cos_key: str = Field(..., max_length=1024, description="COS 对象 Key")
