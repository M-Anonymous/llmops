from fastapi import Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.component.database.postgres_client import get_pg_session
from app.entity.library.library import LibraryInfo
from app.request.library.library import LibraryDeleteRequest, LibraryRequest, LibraryUpdateRequest
from app.service.oauth.current_user import CurrentUser


class LibraryService:

    def __init__(self, account_id: int, db: AsyncSession):
        self.db = db
        self.account_id = account_id

    async def _get_owned_library(self, library_id: str) -> LibraryInfo:
        result = await self.db.execute(
            select(LibraryInfo).where(
                LibraryInfo.id == library_id,
                LibraryInfo.account_id == self.account_id,
            )
        )
        entity = result.scalar_one_or_none()
        if not entity:
            raise HTTPException(status_code=404, detail="知识库不存在")
        return entity

    @staticmethod
    def _to_dict(entity: LibraryInfo) -> dict:
        return {
            "id": entity.id,
            "name": entity.name,
            "desc": entity.desc,
            "icon": entity.icon,
            "createAt": entity.createAt,
            "updateAt": entity.updateAt,
        }

    async def create_library(self, request: LibraryRequest) -> str:
        data = request.model_dump(exclude_unset=True)
        entity = LibraryInfo(account_id=self.account_id, **data)
        self.db.add(entity)
        await self.db.commit()
        await self.db.refresh(entity)
        return entity.id

    async def delete_library(self, request: LibraryDeleteRequest) -> None:
        entity = await self._get_owned_library(request.id)
        await self.db.delete(entity)
        await self.db.commit()

    async def update_library(self, request: LibraryUpdateRequest) -> dict:
        entity = await self._get_owned_library(request.id)
        data = request.model_dump(exclude_unset=True, exclude={"id"})
        if not data:
            raise HTTPException(status_code=400, detail="未提供需要更新的字段")
        for key, value in data.items():
            setattr(entity, key, value)
        await self.db.commit()
        await self.db.refresh(entity)
        return self._to_dict(entity)

    async def get_library_list(self) -> list[dict]:
        result = await self.db.execute(
            select(LibraryInfo)
            .where(LibraryInfo.account_id == self.account_id)
            .order_by(LibraryInfo.createAt.desc())
        )
        libraries = result.scalars().all()
        return [self._to_dict(library) for library in libraries]


async def get_library_service(
    account_id: int = Depends(CurrentUser()),
    db: AsyncSession = Depends(get_pg_session),
) -> LibraryService:
    return LibraryService(account_id, db)
