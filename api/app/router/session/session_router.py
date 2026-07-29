from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse

from app.request.session.session_request import SessionRequest, SessionResumeRequest
from app.service.session.session_service import SessionService, get_session_service

session_router = APIRouter(prefix="/session", tags=["session"])


@session_router.post("/create")
async def create_session(
    request: SessionRequest,
    session_service: SessionService = Depends(get_session_service),
):
    session_id = await session_service.create_session(request)
    return {"id": session_id}


@session_router.post("/delete")
async def delete_session(
    request: SessionRequest,
    session_service: SessionService = Depends(get_session_service),
):
    await session_service.delete_session(request)
    return {"status": "success"}


@session_router.post("/update")
async def update_session(
    request: SessionRequest,
    session_service: SessionService = Depends(get_session_service),
):
    return await session_service.update_session(request)


@session_router.get("/list")
async def get_session_list(
    agent_id: str | None = Query(default=None, description="按 Agent 过滤"),
    visitor_id: str | None = Query(default=None, description="访客 id；未登录时必填"),
    session_service: SessionService = Depends(get_session_service),
):
    return await session_service.get_session_list(
        agent_id=agent_id,
        visitor_id=visitor_id,
    )


@session_router.get("/messages")
async def get_session_messages(
    session_id: str = Query(..., description="会话 ID"),
    visitor_id: str | None = Query(default=None, description="访客 id；未登录时必填"),
    session_service: SessionService = Depends(get_session_service),
):
    return await session_service.get_session_messages(
        session_id=session_id,
        visitor_id=visitor_id,
    )


@session_router.post("/chat")
async def session_chat(
    request: SessionRequest,
    session_service: SessionService = Depends(get_session_service),
):
    return await session_service.chat(request)


@session_router.post("/stream")
async def session_stream(
    request: SessionRequest,
    session_service: SessionService = Depends(get_session_service),
):
    # 无 session_id 时先创建会话，再开始 SSE（保证校验错误能正常返回）
    session_id, agent_id = await session_service.prepare_stream(request)
    return StreamingResponse(
        session_service.stream(request, session_id, agent_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@session_router.post("/resume")
async def session_resume(
    request: SessionResumeRequest,
    session_service: SessionService = Depends(get_session_service),
):
    session_id, agent_id = await session_service.prepare_resume(request)
    return StreamingResponse(
        session_service.resume_stream(request, session_id, agent_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
