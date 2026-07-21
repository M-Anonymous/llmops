from fastapi import Depends

from app.request.session.session_request import SessionRequest
from app.repository.session.session_repository import SessionRepository, get_session_repository
from app.agent.pool.agent_session_pool import AgentSessionPool
from app.agent.tool.builtin_tool.memory_tool import Context


class SessionService:


    def __init__(self, session_repository: SessionRepository):
        self.session_repository = session_repository


    async def chat(self,request: SessionRequest):
        #判断会话id是否存在

        #不存在新建会话
        #session_id = await self.session_repository.create_session()

        agent = AgentSessionPool.get_or_create_agent(request.session_id,request.agent_id)

        return agent.invoke(
            {"messages":[{"role":"user","content":request.question}]},
            config={"configurable":{"thread_id":request.session_id}},
            context=Context(account_id=122222222)
        )


    async def stream(self):
        pass


async def get_session_service(session_repository: SessionRepository = Depends(get_session_repository)):
    return SessionService(session_repository)
