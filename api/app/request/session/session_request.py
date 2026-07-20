from pydantic import BaseModel, Field


class SessionRequest(BaseModel):
    agent_id: str = Field(..., max_length=255, description="agent id")
    session_id : str = Field(..., max_length=255, description="会话 id")
    question: str = Field(..., max_length=255, description="用户问题")