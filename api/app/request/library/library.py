from typing import Any, Optional

from pydantic import BaseModel, Field

from app.agent.document.splitter.support.support_splitter import SupportSplitter

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


class DocumentUpdateStatusRequest(BaseModel):
    """文档状态更新请求模型"""

    id: str = Field(..., description="文档ID")
    status: int = Field(
        ...,
        description="文件状态: 0 unprocess, 1 load, 2 clean, 3 split, 4 complete",
    )


class DocumentParseRequest(BaseModel):
    """文档解析请求模型"""

    id: str = Field(..., description="文档ID")
    splitter_type: SupportSplitter = Field(
        default=SupportSplitter.DEFAULT,
        description="分割器类型: default / md",
    )
    splitter_params: dict[str, Any] = Field(
        default_factory=dict,
        description="分割器参数，如 chunk_size、chunk_overlap",
    )


class ChunkItem(BaseModel):
    """文档分片内容项"""

    position: int = Field(..., description="片段在文档中的位置")
    content: str = Field(..., description="片段内容")
    hash: str = Field(..., max_length=255, description="内容哈希值")
    enabled: bool = Field(default=True, description="是否启用")


class ChunkAddRequest(BaseModel):
    """文档分片添加请求模型"""

    document_id: str = Field(..., description="所属文档ID")
    position: int = Field(..., description="片段在文档中的位置")
    content: str = Field(..., description="片段内容")
    hash: str = Field(..., max_length=255, description="内容哈希值")
    enabled: bool = Field(default=True, description="是否启用")


class ChunkBatchAddRequest(BaseModel):
    """文档分片批量添加请求模型"""

    document_id: str = Field(..., description="所属文档ID")
    chunks: list[ChunkItem] = Field(..., min_length=1, description="分片列表")


class ChunkDeleteRequest(BaseModel):
    """文档分片删除请求模型"""

    id: str = Field(..., description="分片ID")


class ChunkUpdateRequest(BaseModel):
    """文档分片更新请求模型"""

    id: str = Field(..., description="分片ID")
    position: Optional[int] = Field(default=None, description="片段在文档中的位置")
    content: Optional[str] = Field(default=None, description="片段内容")
    hash: Optional[str] = Field(default=None, max_length=255, description="内容哈希值")
    enabled: Optional[bool] = Field(default=None, description="是否启用")
