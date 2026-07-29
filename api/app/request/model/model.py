from typing import Optional

from pydantic import BaseModel, Field


class ModelCreateRequest(BaseModel):
    """模型创建请求模型"""

    name: str = Field(..., max_length=100, description="模型名称，如 gpt-4o")
    label: str = Field(..., max_length=100, description="模型显示名称")
    desc: str = Field(..., max_length=255, description="模型描述")
    api_key: str = Field(..., max_length=512, description="API Key")
    base_url: str = Field(..., max_length=255, description="调用地址")
    icon: Optional[str] = Field(default=None, max_length=255, description="模型图标")


class ModelUpdateRequest(BaseModel):
    """模型更新请求模型"""

    id: str = Field(..., description="模型 ID")
    name: Optional[str] = Field(default=None, max_length=100, description="模型名称")
    label: Optional[str] = Field(default=None, max_length=100, description="模型显示名称")
    desc: Optional[str] = Field(default=None, max_length=255, description="模型描述")
    api_key: Optional[str] = Field(default=None, max_length=512, description="API Key")
    base_url: Optional[str] = Field(default=None, max_length=255, description="调用地址")
    icon: Optional[str] = Field(default=None, max_length=255, description="模型图标")


class ModelDeleteRequest(BaseModel):
    """模型删除请求模型"""

    id: str = Field(..., description="模型 ID")
