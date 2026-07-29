from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.component.database.postgres_client import get_pg_session
from app.entity.session.session import SessionInfo


class SessionRepository:

    def __init__(self, db: AsyncSession):
        self.db = db

    async def find_session(self, session_id: str) -> SessionInfo | None:
        result = await self.db.execute(
            select(SessionInfo).where(SessionInfo.id == session_id)
        )
        return result.scalar_one_or_none()

    async def find_session_by_account(
        self,
        session_id: str,
        account_id: int,
    ) -> SessionInfo | None:
        result = await self.db.execute(
            select(SessionInfo).where(
                SessionInfo.id == session_id,
                SessionInfo.account_id == account_id,
            )
        )
        return result.scalar_one_or_none()

    async def find_session_by_visitor(
        self,
        session_id: str,
        visitor_id: str,
    ) -> SessionInfo | None:
        result = await self.db.execute(
            select(SessionInfo).where(
                SessionInfo.id == session_id,
                SessionInfo.visitor_id == visitor_id,
            )
        )
        return result.scalar_one_or_none()

    async def list_sessions_by_account(
        self,
        account_id: int,
        agent_id: str | None = None,
    ) -> list[SessionInfo]:
        stmt = select(SessionInfo).where(SessionInfo.account_id == account_id)
        if agent_id:
            stmt = stmt.where(SessionInfo.agent_id == agent_id)
        stmt = stmt.order_by(SessionInfo.update_at.desc())
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def list_sessions_by_visitor(
        self,
        visitor_id: str,
        agent_id: str | None = None,
    ) -> list[SessionInfo]:
        stmt = select(SessionInfo).where(SessionInfo.visitor_id == visitor_id)
        if agent_id:
            stmt = stmt.where(SessionInfo.agent_id == agent_id)
        stmt = stmt.order_by(SessionInfo.update_at.desc())
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def add_session(self, entity: SessionInfo) -> SessionInfo:
        self.db.add(entity)
        await self.db.commit()
        await self.db.refresh(entity)
        return entity

    async def update_session(self, entity: SessionInfo) -> SessionInfo:
        await self.db.commit()
        await self.db.refresh(entity)
        return entity

    async def delete_session(self, entity: SessionInfo) -> None:
        await self.db.delete(entity)
        await self.db.commit()


async def get_session_repository(
    db: AsyncSession = Depends(get_pg_session),
) -> SessionRepository:
    return SessionRepository(db)
