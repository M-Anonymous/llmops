from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.component.database.postgres_client import get_pg_session
from app.entity.tool.tool_entity import ApiToolEntity, ApiToolRelation


class APIToolRepository:

    def __init__(self, db: AsyncSession):
        self.db = db

    async def find_tool(self, tool_id: str, account_id: int) -> ApiToolEntity | None:
        result = await self.db.execute(
            select(ApiToolEntity)
            .join(ApiToolRelation, ApiToolEntity.id == ApiToolRelation.tool_id)
            .where(
                ApiToolEntity.id == tool_id,
                ApiToolRelation.account_id == account_id,
            )
        )
        return result.scalar_one_or_none()

    async def find_relation(
        self,
        tool_id: str,
        account_id: int,
    ) -> ApiToolRelation | None:
        result = await self.db.execute(
            select(ApiToolRelation).where(
                ApiToolRelation.tool_id == tool_id,
                ApiToolRelation.account_id == account_id,
            )
        )
        return result.scalar_one_or_none()

    async def add_tool_with_relation(
        self,
        entity: ApiToolEntity,
        relation: ApiToolRelation,
    ) -> ApiToolEntity:
        self.db.add(entity)
        await self.db.flush()
        self.db.add(relation)
        await self.db.commit()
        await self.db.refresh(entity)
        return entity

    async def list_tools_by_account(self, account_id: int) -> list[ApiToolEntity]:
        result = await self.db.execute(
            select(ApiToolEntity)
            .join(ApiToolRelation, ApiToolEntity.id == ApiToolRelation.tool_id)
            .where(ApiToolRelation.account_id == account_id)
            .order_by(ApiToolEntity.create_at.desc())
        )
        return list(result.scalars().all())

    async def update_tool(self, entity: ApiToolEntity) -> ApiToolEntity:
        await self.db.commit()
        await self.db.refresh(entity)
        return entity

    async def delete_tool_with_relation(
        self,
        entity: ApiToolEntity,
        relation: ApiToolRelation,
    ) -> None:
        await self.db.delete(relation)
        await self.db.delete(entity)
        await self.db.commit()


async def get_api_tool_repository(
    db: AsyncSession = Depends(get_pg_session),
) -> APIToolRepository:
    return APIToolRepository(db)
