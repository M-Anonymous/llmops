from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from app.request.agent.agent import (
    AgentCreateRequest,
    AgentDebugChatRequest,
    AgentDeleteRequest,
    AgentUpdateRequest,
)
from app.request.session.session_request import SessionRequest
from app.service.agent.agent_service import AgentService, get_agent_service
from app.service.session.session_service import SessionService, get_session_service

agent_router = APIRouter(prefix="/agent", tags=["agent"])

_DEBUG_SESSION_TITLE = "调试会话"


@agent_router.post("/create")
async def create_agent(
    request: AgentCreateRequest,
    agent_service: AgentService = Depends(get_agent_service),
):
    agent_id = await agent_service.create_agent(request)
    return {"id": agent_id}


@agent_router.post("/delete")
async def delete_agent(
    request: AgentDeleteRequest,
    agent_service: AgentService = Depends(get_agent_service),
):
    await agent_service.delete_agent(request)
    return {"status": "success"}


@agent_router.post("/update")
async def update_agent(
    request: AgentUpdateRequest,
    agent_service: AgentService = Depends(get_agent_service),
):
    return await agent_service.update_agent(request)


@agent_router.get("/list")
async def get_agent_list(
    agent_service: AgentService = Depends(get_agent_service),
):
    return await agent_service.get_agent_list()


@agent_router.post("/debug/chat")
async def debug_chat(
    request: AgentDebugChatRequest,
    agent_service: AgentService = Depends(get_agent_service),
    session_service: SessionService = Depends(get_session_service),
):
    """调试对话：校验 Agent 归属后走会话 chat。"""
    await agent_service.get_agent(request.agent_id)
    return await session_service.chat(
        SessionRequest(
            agent_id=request.agent_id,
            question=request.question,
            session_id=request.session_id,
            title=_DEBUG_SESSION_TITLE,
        )
    )


@agent_router.post("/debug/stream")
async def debug_stream(
    request: AgentDebugChatRequest,
    agent_service: AgentService = Depends(get_agent_service),
    session_service: SessionService = Depends(get_session_service),
):
    """调试对话流式输出。"""
    await agent_service.get_agent(request.agent_id)
    session_request = SessionRequest(
        agent_id=request.agent_id,
        question=request.question,
        session_id=request.session_id,
        title=_DEBUG_SESSION_TITLE,
    )
    session_id, agent_id = await session_service.prepare_stream(session_request)
    return StreamingResponse(
        session_service.stream(session_request, session_id, agent_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
