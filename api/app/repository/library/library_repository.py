from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.component.database.postgres_client import get_pg_session
from app.entity.library.library import LibraryInfo


class LibraryRepository:

    def __init__(self, db: AsyncSession):
        self.db = db

    async def find_library(self, library_id: str, account_id: int) -> LibraryInfo | None:
        result = await self.db.execute(
            select(LibraryInfo).where(
                LibraryInfo.id == library_id,
                LibraryInfo.account_id == account_id,
            )
        )
        return result.scalar_one_or_none()

    async def list_libraries(self, account_id: int) -> list[LibraryInfo]:
        result = await self.db.execute(
            select(LibraryInfo)
            .where(LibraryInfo.account_id == account_id)
            .order_by(LibraryInfo.create_at.desc())
        )
        return list(result.scalars().all())

    async def add_library(self, entity: LibraryInfo) -> LibraryInfo:
        self.db.add(entity)
        await self.db.commit()
        await self.db.refresh(entity)
        return entity

    async def delete_library(self, entity: LibraryInfo) -> None:
        await self.db.delete(entity)
        await self.db.commit()

    async def update_library(self, entity: LibraryInfo) -> LibraryInfo:
        await self.db.commit()
        await self.db.refresh(entity)
        return entity


async def get_library_repository(
    db: AsyncSession = Depends(get_pg_session),
) -> LibraryRepository:
    return LibraryRepository(db)
