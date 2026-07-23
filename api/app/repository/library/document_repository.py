from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.component.database.postgres_client import get_pg_session
from app.entity.library.library import DocumentInfo, LibraryInfo


class DocumentRepository:

    def __init__(self, db: AsyncSession):
        self.db = db

    async def find_document(self, document_id: str, account_id: int) -> DocumentInfo | None:
        result = await self.db.execute(
            select(DocumentInfo)
            .join(LibraryInfo, DocumentInfo.library_id == LibraryInfo.id)
            .where(
                DocumentInfo.id == document_id,
                LibraryInfo.account_id == account_id,
            )
        )
        return result.scalar_one_or_none()

    async def list_documents(self, library_id: str) -> list[DocumentInfo]:
        result = await self.db.execute(
            select(DocumentInfo)
            .where(DocumentInfo.library_id == library_id)
            .order_by(DocumentInfo.create_at.desc())
        )
        return list(result.scalars().all())

    async def add_document(self, entity: DocumentInfo) -> DocumentInfo:
        self.db.add(entity)
        await self.db.commit()
        await self.db.refresh(entity)
        return entity

    async def delete_document(self, entity: DocumentInfo) -> None:
        await self.db.delete(entity)
        await self.db.commit()


async def get_document_repository(
    db: AsyncSession = Depends(get_pg_session),
) -> DocumentRepository:
    return DocumentRepository(db)
