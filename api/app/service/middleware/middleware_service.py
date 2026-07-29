from fastapi import Depends, HTTPException

from app.entity.middleware.middleware import MiddlewareInfo
from app.repository.middleware.middleware_repository import (
    MiddlewareRepository,
    get_middleware_repository,
)
from app.request.middleware.middleware import (
    MiddlewareCreateRequest,
    MiddlewareDeleteRequest,
    MiddlewareUpdateRequest,
)
from app.service.oauth.current_user import CurrentUser


class MiddlewareService:

    def __init__(self, account_id: int, middleware_repository: MiddlewareRepository):
        self.account_id = account_id
        self.middleware_repository = middleware_repository

    @staticmethod
    def _to_dict(entity: MiddlewareInfo) -> dict:
        return {
            "id": entity.id,
            "accountId": entity.account_id,
            "label": entity.label,
            "type": entity.type,
            "config": entity.config,
            "createAt": entity.create_at,
            "updateAt": entity.update_at,
        }

    async def get_middleware(self, middleware_id: str) -> MiddlewareInfo:
        entity = await self.middleware_repository.find_middleware(
            middleware_id, self.account_id
        )
        if not entity:
            raise HTTPException(status_code=404, detail="中间件不存在")
        return entity

    async def create_middleware(self, request: MiddlewareCreateRequest) -> str:
        entity = MiddlewareInfo(
            account_id=self.account_id,
            label=request.label,
            type=request.type,
            config=request.config,
        )
        created = await self.middleware_repository.add_middleware(entity)
        return created.id

    async def update_middleware(self, request: MiddlewareUpdateRequest) -> dict:
        entity = await self.get_middleware(request.id)
        data = request.model_dump(exclude_unset=True, exclude={"id"})
        if not data:
            raise HTTPException(status_code=400, detail="未提供需要更新的字段")
        for key, value in data.items():
            setattr(entity, key, value)
        updated = await self.middleware_repository.update_middleware(entity)
        return self._to_dict(updated)

    async def delete_middleware(self, request: MiddlewareDeleteRequest) -> None:
        entity = await self.get_middleware(request.id)
        await self.middleware_repository.delete_middleware(entity)

    async def get_middleware_list(self) -> list[dict]:
        middlewares = await self.middleware_repository.list_middlewares(self.account_id)
        return [self._to_dict(item) for item in middlewares]


async def get_middleware_service(
    account_id: int = Depends(CurrentUser()),
    middleware_repository: MiddlewareRepository = Depends(get_middleware_repository),
) -> MiddlewareService:
    return MiddlewareService(account_id, middleware_repository)
