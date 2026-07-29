from typing import Optional

from pydantic import BaseModel, Field


class AgentCreateRequest(BaseModel):
    """Agent 创建请求模型"""

    name: str = Field(..., max_length=100, description="Agent 名称")
    desc: str = Field(..., max_length=255, description="Agent 描述")
    icon: Optional[str] = Field(default=None, max_length=255, description="Agent 图标")
    system_prompt: Optional[str] = Field(default=None, description="系统提示词")
    model_id: Optional[str] = Field(default=None, max_length=36, description="关联的模型 ID")
    library_ids: list[str] = Field(default_factory=list, description="关联的知识库 ID 列表")
    tool_ids: list[str] = Field(default_factory=list, description="关联的工具 ID 列表")
    middleware_ids: list[str] = Field(default_factory=list, description="关联的中间件 ID 列表")


class AgentUpdateRequest(BaseModel):
    """Agent 更新请求模型"""

    id: str = Field(..., description="Agent ID")
    name: Optional[str] = Field(default=None, max_length=100, description="Agent 名称")
    desc: Optional[str] = Field(default=None, max_length=255, description="Agent 描述")
    icon: Optional[str] = Field(default=None, max_length=255, description="Agent 图标")
    system_prompt: Optional[str] = Field(default=None, description="系统提示词")
    model_id: Optional[str] = Field(default=None, max_length=36, description="关联的模型 ID")
    library_ids: Optional[list[str]] = Field(default=None, description="关联的知识库 ID 列表")
    tool_ids: Optional[list[str]] = Field(default=None, description="关联的工具 ID 列表")
    middleware_ids: Optional[list[str]] = Field(default=None, description="关联的中间件 ID 列表")


class AgentDeleteRequest(BaseModel):
    """Agent 删除请求模型"""

    id: str = Field(..., description="Agent ID")


class AgentDebugChatRequest(BaseModel):
    """Agent 调试对话请求"""

    agent_id: str = Field(..., max_length=36, description="Agent ID")
    question: str = Field(..., min_length=1, max_length=8000, description="用户问题")
    session_id: Optional[str] = Field(
        default=None,
        max_length=36,
        description="会话 id，不传则自动新建调试会话",
    )
