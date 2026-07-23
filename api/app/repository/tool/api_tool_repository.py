from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.component.database.postgres_client import get_pg_session
from app.entity.tool.tool_entity import ApiToolEntity, ApiToolRelation


class APIToolRepository:

    def __init__(self, db: AsyncSession):
        self.db = db

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


async def get_api_tool_repository(
    db: AsyncSession = Depends(get_pg_session),
) -> APIToolRepository:
    return APIToolRepository(db)
