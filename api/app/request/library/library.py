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
