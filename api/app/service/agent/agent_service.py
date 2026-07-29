from fastapi import Depends, HTTPException

from app.entity.agent.agent import AgentConfig
from app.repository.agent.agent_repository import AgentRepository, get_agent_repository
from app.request.agent.agent import (
    AgentCreateRequest,
    AgentDeleteRequest,
    AgentUpdateRequest,
)
from app.service.oauth.current_user import CurrentUser


class AgentService:

    def __init__(self, account_id: int, agent_repository: AgentRepository):
        self.account_id = account_id
        self.agent_repository = agent_repository

    @staticmethod
    def _to_dict(entity: AgentConfig) -> dict:
        return {
            "id": entity.id,
            "accountId": entity.account_id,
            "name": entity.name,
            "desc": entity.desc,
            "icon": entity.icon,
            "systemPrompt": entity.system_prompt,
            "modelId": entity.model_id,
            "libraryIds": entity.library_ids or [],
            "toolIds": entity.tool_ids or [],
            "middlewareIds": entity.middleware_ids or [],
            "createAt": entity.create_at,
            "updateAt": entity.update_at,
        }

    async def get_agent(self, agent_id: str) -> AgentConfig:
        entity = await self.agent_repository.find_agent(agent_id, self.account_id)
        if not entity:
            raise HTTPException(status_code=404, detail="Agent 不存在")
        return entity

    async def create_agent(self, request: AgentCreateRequest) -> str:
        data = request.model_dump(exclude_unset=True)
        entity = AgentConfig(account_id=self.account_id, **data)
        created = await self.agent_repository.add_agent(entity)
        return created.id

    async def update_agent(self, request: AgentUpdateRequest) -> dict:
        entity = await self.get_agent(request.id)
        data = request.model_dump(exclude_unset=True, exclude={"id"})
        if not data:
            raise HTTPException(status_code=400, detail="未提供需要更新的字段")
        for key, value in data.items():
            setattr(entity, key, value)
        updated = await self.agent_repository.update_agent(entity)
        return self._to_dict(updated)

    async def delete_agent(self, request: AgentDeleteRequest) -> None:
        entity = await self.get_agent(request.id)
        await self.agent_repository.delete_agent(entity)

    async def get_agent_list(self) -> list[dict]:
        agents = await self.agent_repository.list_agents(self.account_id)
        return [self._to_dict(agent) for agent in agents]


async def get_agent_service(
    account_id: int = Depends(CurrentUser()),
    agent_repository: AgentRepository = Depends(get_agent_repository),
) -> AgentService:
    return AgentService(account_id, agent_repository)
