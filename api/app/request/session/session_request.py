from typing import Literal, Optional

from pydantic import BaseModel, Field


class SessionRequest(BaseModel):
    """会话统一请求：创建 / 更新 / 删除 / 聊天 / 流式共用。"""

    session_id: Optional[str] = Field(
        default=None,
        max_length=36,
        description="会话 ID；更新、删除、续聊时必填，创建时可省略",
    )
    agent_id: Optional[str] = Field(
        default=None,
        max_length=64,
        description="Agent ID；新建会话或聊天时按需填写",
    )
    title: Optional[str] = Field(
        default=None,
        max_length=255,
        description="会话标题",
    )
    visitor_id: Optional[str] = Field(
        default=None,
        max_length=36,
        description="访客 id；未登录创建会话时必填",
    )
    question: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=8000,
        description="用户问题；聊天 / 流式时必填",
    )


class HitlDecision(BaseModel):
    """人在回路决策。"""

    type: Literal["approve", "reject"] = Field(..., description="approve / reject")
    message: Optional[str] = Field(
        default=None,
        max_length=2000,
        description="reject 时可选反馈信息",
    )


class SessionResumeRequest(BaseModel):
    """恢复被 HumanInTheLoop 中断的会话。"""

    session_id: str = Field(..., max_length=36, description="会话 ID")
    agent_id: Optional[str] = Field(
        default=None,
        max_length=64,
        description="Agent ID；不传则使用会话上的 agent_id",
    )
    visitor_id: Optional[str] = Field(
        default=None,
        max_length=36,
        description="访客 id；未登录时必填",
    )
    decisions: list[HitlDecision] = Field(
        ...,
        min_length=1,
        description="决策列表，顺序须与 interrupt.actionRequests 一致",
    )
