from typing import Optional

from pydantic import BaseModel, Field

"""
request example:
{
    "name": "产品文档库",
    "desc": "存放产品相关文档",
    "icon": "https://example.com/icon.png"
}
"""


class LibraryRequest(BaseModel):
    """知识库创建请求模型"""

    name: str = Field(
        ...,
        max_length=100,
        description="知识库名称"
    )
    desc: str = Field(
        ...,
        max_length=50,
        description="知识库描述"
    )
    icon: Optional[str] = Field(
        default=None,
        max_length=255,
        description="知识库图标"
    )


class LibraryUpdateRequest(BaseModel):
    """知识库更新请求模型"""

    id: str = Field(..., description="知识库ID")
    name: Optional[str] = Field(default=None, max_length=100, description="知识库名称")
    desc: Optional[str] = Field(default=None, max_length=50, description="知识库描述")
    icon: Optional[str] = Field(default=None, max_length=255, description="知识库图标")


class LibraryDeleteRequest(BaseModel):
    """知识库删除请求模型"""

    id: str = Field(..., description="知识库ID")


class DocumentAddRequest(BaseModel):
    """文档添加请求模型"""

    library_id: str = Field(..., description="所属知识库ID")
    file_name: str = Field(..., max_length=255, description="文件名（不含后缀）")
    file_ext: str = Field(..., max_length=36, description="文件后缀，如 pdf 或 .pdf")
    desc: str = Field(..., max_length=255, description="文档描述")
    file_key: str = Field(..., max_length=255, description="COS 对象 Key，即预上传接口返回的 cos_key")


class DocumentDeleteRequest(BaseModel):
    """文档删除请求模型"""

    id: str = Field(..., description="文档ID")


class DocumentDownloadRequest(BaseModel):
    """文档下载请求模型"""

    id: str = Field(..., description="文档ID")
