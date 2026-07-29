from typing import Any, Optional

from pydantic import BaseModel, Field


class MiddlewareCreateRequest(BaseModel):
    """中间件创建请求模型"""

    label: str = Field(..., max_length=255, description="中间件显示名称")
    type: int = Field(
        ...,
        ge=0,
        le=1,
        description="中间件类型 0:SummarizationMiddleware 1:HumanInTheLoopMiddleware",
    )
    config: dict[str, Any] = Field(..., description="中间件配置")


class MiddlewareUpdateRequest(BaseModel):
    """中间件更新请求模型"""

    id: str = Field(..., description="中间件 ID")
    label: Optional[str] = Field(default=None, max_length=255, description="中间件显示名称")
    type: Optional[int] = Field(
        default=None,
        ge=0,
        le=1,
        description="中间件类型 0:SummarizationMiddleware 1:HumanInTheLoopMiddleware",
    )
    config: Optional[dict[str, Any]] = Field(default=None, description="中间件配置")


class MiddlewareDeleteRequest(BaseModel):
    """中间件删除请求模型"""

    id: str = Field(..., description="中间件 ID")
