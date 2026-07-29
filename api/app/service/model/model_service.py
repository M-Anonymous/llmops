from fastapi import Depends, HTTPException

from app.entity.model.model import ModelInfo
from app.repository.model.model_repository import ModelRepository, get_model_repository
from app.request.model.model import (
    ModelCreateRequest,
    ModelDeleteRequest,
    ModelUpdateRequest,
)
from app.service.oauth.current_user import CurrentUser


class ModelService:

    def __init__(self, account_id: int, model_repository: ModelRepository):
        self.account_id = account_id
        self.model_repository = model_repository

    @staticmethod
    def _to_dict(entity: ModelInfo) -> dict:
        return {
            "id": entity.id,
            "accountId": entity.account_id,
            "name": entity.name,
            "label": entity.label,
            "desc": entity.desc,
            "icon": entity.icon,
            "apiKey": entity.api_key,
            "baseUrl": entity.base_url,
            "createAt": entity.create_at,
            "updateAt": entity.update_at,
        }

    async def get_model(self, model_id: str) -> ModelInfo:
        entity = await self.model_repository.find_model(model_id, self.account_id)
        if not entity:
            raise HTTPException(status_code=404, detail="模型不存在")
        return entity

    async def create_model(self, request: ModelCreateRequest) -> str:
        data = request.model_dump(exclude_unset=True)
        entity = ModelInfo(account_id=self.account_id, **data)
        created = await self.model_repository.add_model(entity)
        return created.id

    async def update_model(self, request: ModelUpdateRequest) -> dict:
        entity = await self.get_model(request.id)
        data = request.model_dump(exclude_unset=True, exclude={"id"})
        if not data:
            raise HTTPException(status_code=400, detail="未提供需要更新的字段")
        for key, value in data.items():
            setattr(entity, key, value)
        updated = await self.model_repository.update_model(entity)
        return self._to_dict(updated)

    async def delete_model(self, request: ModelDeleteRequest) -> None:
        entity = await self.get_model(request.id)
        await self.model_repository.delete_model(entity)

    async def get_model_list(self) -> list[dict]:
        models = await self.model_repository.list_models(self.account_id)
        return [self._to_dict(model) for model in models]


async def get_model_service(
    account_id: int = Depends(CurrentUser()),
    model_repository: ModelRepository = Depends(get_model_repository),
) -> ModelService:
    return ModelService(account_id, model_repository)
