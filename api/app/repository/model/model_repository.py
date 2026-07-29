from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.component.database.postgres_client import get_pg_session
from app.entity.model.model import ModelInfo


class ModelRepository:

    def __init__(self, db: AsyncSession):
        self.db = db

    async def find_model(self, model_id: str, account_id: int) -> ModelInfo | None:
        result = await self.db.execute(
            select(ModelInfo).where(
                ModelInfo.id == model_id,
                ModelInfo.account_id == account_id,
            )
        )
        return result.scalar_one_or_none()

    async def list_models(self, account_id: int) -> list[ModelInfo]:
        result = await self.db.execute(
            select(ModelInfo)
            .where(ModelInfo.account_id == account_id)
            .order_by(ModelInfo.create_at.desc())
        )
        return list(result.scalars().all())

    async def add_model(self, entity: ModelInfo) -> ModelInfo:
        self.db.add(entity)
        await self.db.commit()
        await self.db.refresh(entity)
        return entity

    async def update_model(self, entity: ModelInfo) -> ModelInfo:
        await self.db.commit()
        await self.db.refresh(entity)
        return entity

    async def delete_model(self, entity: ModelInfo) -> None:
        await self.db.delete(entity)
        await self.db.commit()


async def get_model_repository(
    db: AsyncSession = Depends(get_pg_session),
) -> ModelRepository:
    return ModelRepository(db)
