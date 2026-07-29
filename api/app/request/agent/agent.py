from typing import Any, Optional

from pydantic import BaseModel, Field


class AgentRuntimeConfig(BaseModel):
    """Agent 运行时 LLM 参数。"""

    preset: str = Field(
        default="balanced",
        description="预设：creative（创意）| balanced（平衡）| precise（精确）| custom",
    )
    temperature: Optional[float] = Field(default=None, ge=0, le=2, description="custom 时可覆盖")
    top_p: Optional[float] = Field(default=None, ge=0, le=1, description="custom 时可覆盖")
    max_tokens: Optional[int] = Field(default=None, ge=1, description="custom 时可覆盖")


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
    mcp_server_ids: list[str] = Field(default_factory=list, description="关联的 MCP Server ID 列表")
    runtime_config: Optional[dict[str, Any]] = Field(default=None, description="运行时 LLM 参数")
    mcp_tool_cache: Optional[dict[str, list[str]]] = Field(
        default=None,
        description="MCP 工具选择 {server_id: [tool_name]}",
    )


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
    mcp_server_ids: Optional[list[str]] = Field(default=None, description="关联的 MCP Server ID 列表")
    runtime_config: Optional[dict[str, Any]] = Field(default=None, description="运行时 LLM 参数")
    mcp_tool_cache: Optional[dict[str, list[str]]] = Field(
        default=None,
        description="MCP 工具选择 {server_id: [tool_name]}",
    )


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
