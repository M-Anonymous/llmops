from fastapi import Depends, HTTPException

from app.entity import ApiToolEntity
from app.entity.tool.tool_entity import ApiToolRelation
from app.repository.tool.api_tool_repository import (
    APIToolRepository,
    get_api_tool_repository,
)
from app.request.tool.tool import (
    ApiToolDeleteRequest,
    ApiToolRequest,
    ApiToolUpdateRequest,
)
from app.service.oauth.current_user import CurrentUser


class ApiToolService:

    def __init__(self, account_id: int, api_tool_repository: APIToolRepository):
        self.account_id = account_id
        self.api_tool_repository = api_tool_repository

    @staticmethod
    def _to_dict(entity: ApiToolEntity) -> dict:
        return {
            "id": entity.id,
            "name": entity.name,
            "label": entity.label,
            "desc": entity.desc,
            "apiConfig": entity.api_config,
            "enabled": entity.enabled,
            "createAt": entity.create_at,
            "updateAt": entity.update_at,
        }

    async def get_tool(self, tool_id: str) -> ApiToolEntity:
        entity = await self.api_tool_repository.find_tool(tool_id, self.account_id)
        if not entity:
            raise HTTPException(status_code=404, detail="工具不存在")
        return entity

    async def add_tool(self, request: ApiToolRequest) -> str:
        data = request.model_dump(exclude_unset=True)
        entity = ApiToolEntity(
            **data,
            createBy=self.account_id,
            updateBy=self.account_id,
        )
        relation = ApiToolRelation(
            account_id=self.account_id,
            tool_id=entity.id,
        )
        created = await self.api_tool_repository.add_tool_with_relation(entity, relation)
        return created.id

    async def update_tool(self, request: ApiToolUpdateRequest) -> dict:
        entity = await self.get_tool(request.id)
        data = request.model_dump(exclude_unset=True, exclude={"id"})
        if not data:
            raise HTTPException(status_code=400, detail="未提供需要更新的字段")
        for key, value in data.items():
            setattr(entity, key, value)
        entity.updateBy = self.account_id
        updated = await self.api_tool_repository.update_tool(entity)
        return self._to_dict(updated)

    async def delete_tool(self, request: ApiToolDeleteRequest) -> None:
        entity = await self.get_tool(request.id)
        relation = await self.api_tool_repository.find_relation(request.id, self.account_id)
        if not relation:
            raise HTTPException(status_code=404, detail="工具关联不存在")
        await self.api_tool_repository.delete_tool_with_relation(entity, relation)

    async def get_tools(self) -> list[ApiToolEntity]:
        return await self.api_tool_repository.list_tools_by_account(self.account_id)

    async def get_tool_list(self) -> list[dict]:
        tools = await self.get_tools()
        return [self._to_dict(tool) for tool in tools]


async def get_api_tool_service(
    account_id: int = Depends(CurrentUser()),
    api_tool_repository: APIToolRepository = Depends(get_api_tool_repository),
) -> ApiToolService:
    return ApiToolService(account_id, api_tool_repository)
