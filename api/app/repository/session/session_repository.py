from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.component.database.postgres_client import get_pg_session


class SessionRepository:

    def __init__(self, db: AsyncSession):
        self.db = db



    async def create_session(self) -> str:
        return "session_id-123478"


    async def delete_session(self):
        pass

    async def update_session(self):
        pass


    async def list_session(self):
        pass


async def get_session_repository(db: AsyncSession = Depends(get_pg_session)) -> SessionRepository:
    return SessionRepository(db)