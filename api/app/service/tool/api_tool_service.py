from fastapi import Depends

from app.entity import ApiToolEntity
from app.entity.tool.tool_entity import ApiToolRelation
from app.repository.tool.api_tool_repository import (
    APIToolRepository,
    get_api_tool_repository,
)
from app.request.tool.tool import ApiToolRequest
from app.service.oauth.current_user import CurrentUser


class ApiToolService:

    def __init__(self, account_id: int, api_tool_repository: APIToolRepository):
        self.account_id = account_id
        self.api_tool_repository = api_tool_repository

    async def add_tool(self, request: ApiToolRequest) -> str:
        data = request.model_dump(exclude_unset=True)
        entity = ApiToolEntity(**data)
        entity.createBy = self.account_id
        entity.updateBy = self.account_id

        relation = ApiToolRelation(
            account_id=self.account_id,
            tool_id=entity.id,
        )
        created = await self.api_tool_repository.add_tool_with_relation(entity, relation)
        return created.id

    async def get_tools(self) -> list[ApiToolEntity]:
        return await self.api_tool_repository.list_tools_by_account(self.account_id)


async def get_api_tool_service(
    account_id: int = Depends(CurrentUser()),
    api_tool_repository: APIToolRepository = Depends(get_api_tool_repository),
) -> ApiToolService:
    return ApiToolService(account_id, api_tool_repository)
