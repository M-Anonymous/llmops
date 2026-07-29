from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.component.database.postgres_client import get_pg_session
from app.entity.middleware.middleware import MiddlewareInfo


class MiddlewareRepository:

    def __init__(self, db: AsyncSession):
        self.db = db

    async def find_middleware(
        self, middleware_id: str, account_id: int
    ) -> MiddlewareInfo | None:
        result = await self.db.execute(
            select(MiddlewareInfo).where(
                MiddlewareInfo.id == middleware_id,
                MiddlewareInfo.account_id == account_id,
            )
        )
        return result.scalar_one_or_none()

    async def list_middlewares(self, account_id: int) -> list[MiddlewareInfo]:
        result = await self.db.execute(
            select(MiddlewareInfo)
            .where(MiddlewareInfo.account_id == account_id)
            .order_by(MiddlewareInfo.create_at.desc())
        )
        return list(result.scalars().all())

    async def list_middlewares_by_ids(self, middleware_ids: list[str]) -> list[MiddlewareInfo]:
        if not middleware_ids:
            return []
        result = await self.db.execute(
            select(MiddlewareInfo).where(MiddlewareInfo.id.in_(middleware_ids))
        )
        return list(result.scalars().all())

    async def add_middleware(self, entity: MiddlewareInfo) -> MiddlewareInfo:
        self.db.add(entity)
        await self.db.commit()
        await self.db.refresh(entity)
        return entity

    async def update_middleware(self, entity: MiddlewareInfo) -> MiddlewareInfo:
        await self.db.commit()
        await self.db.refresh(entity)
        return entity

    async def delete_middleware(self, entity: MiddlewareInfo) -> None:
        await self.db.delete(entity)
        await self.db.commit()


async def get_middleware_repository(
    db: AsyncSession = Depends(get_pg_session),
) -> MiddlewareRepository:
    return MiddlewareRepository(db)
