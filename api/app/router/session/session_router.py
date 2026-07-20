
from fastapi import APIRouter, Depends

from app.request.session.session_request import SessionRequest
from app.service.session.session_service import SessionService, get_session_service

session_router = APIRouter(prefix="/session")


@session_router.post("/chat")
async def session(request: SessionRequest,session_service: SessionService = Depends(get_session_service)):
    return await session_service.chat(request)