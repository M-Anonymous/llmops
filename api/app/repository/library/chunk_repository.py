from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.component.database.postgres_client import get_pg_session
from app.entity.library.library import ChunkInfo


class ChunkRepository:

    def __init__(self, db: AsyncSession):
        self.db = db

    async def find_chunk(self, chunk_id: str) -> ChunkInfo | None:
        result = await self.db.execute(
            select(ChunkInfo).where(ChunkInfo.id == chunk_id)
        )
        return result.scalar_one_or_none()

    async def list_chunks(self, document_id: str) -> list[ChunkInfo]:
        result = await self.db.execute(
            select(ChunkInfo)
            .where(ChunkInfo.document_id == document_id)
            .order_by(ChunkInfo.position.asc())
        )
        return list(result.scalars().all())

    async def add_chunk(self, entity: ChunkInfo) -> ChunkInfo:
        self.db.add(entity)
        await self.db.commit()
        await self.db.refresh(entity)
        return entity

    async def add_chunks(self, entities: list[ChunkInfo]) -> list[ChunkInfo]:
        if not entities:
            return []
        self.db.add_all(entities)
        await self.db.commit()
        for entity in entities:
            await self.db.refresh(entity)
        return entities

    async def update_chunk(self, entity: ChunkInfo) -> ChunkInfo:
        await self.db.commit()
        await self.db.refresh(entity)
        return entity

    async def delete_chunk(self, entity: ChunkInfo) -> None:
        await self.db.delete(entity)
        await self.db.commit()


async def get_chunk_repository(
    db: AsyncSession = Depends(get_pg_session),
) -> ChunkRepository:
    return ChunkRepository(db)
