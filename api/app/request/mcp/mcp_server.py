from typing import Any, Optional

from pydantic import BaseModel, Field


class McpServerCreateRequest(BaseModel):
    """MCP Server 创建请求"""

    name: str = Field(..., max_length=100, description="内部名称（连接键）")
    label: str = Field(..., max_length=255, description="显示名称")
    desc: str = Field(default="", description="描述")
    transport: int = Field(
        default=2,
        ge=2,
        le=2,
        description="传输类型（当前仅支持 2:streamable_http）",
    )
    config: dict[str, Any] = Field(..., description="连接配置")
    enabled: bool = Field(default=True, description="是否启用")


class McpServerUpdateRequest(BaseModel):
    """MCP Server 更新请求"""

    id: str = Field(..., description="MCP Server ID")
    name: Optional[str] = Field(default=None, max_length=100, description="内部名称（连接键）")
    label: Optional[str] = Field(default=None, max_length=255, description="显示名称")
    desc: Optional[str] = Field(default=None, description="描述")
    transport: Optional[int] = Field(
        default=None,
        ge=2,
        le=2,
        description="传输类型（当前仅支持 2:streamable_http）",
    )
    config: Optional[dict[str, Any]] = Field(default=None, description="连接配置")
    enabled: Optional[bool] = Field(default=None, description="是否启用")


class McpServerDeleteRequest(BaseModel):
    """MCP Server 删除请求"""

    id: str = Field(..., description="MCP Server ID")


class McpServerTestRequest(BaseModel):
    """MCP Server 连接测试请求（新建/编辑表单均可用）"""

    name: str = Field(..., max_length=100, description="内部名称（连接键）")
    transport: int = Field(
        default=2,
        ge=2,
        le=2,
        description="传输类型（当前仅支持 2:streamable_http）",
    )
    config: dict[str, Any] = Field(..., description="连接配置")
