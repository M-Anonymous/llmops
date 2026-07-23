from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.component.database.postgres_client import get_pg_session
from app.entity.oauth.account_info import AccountInfo


class AccountRepository:

    def __init__(self, db: AsyncSession):
        self.db = db

    async def find_by_id(self, account_id: int) -> AccountInfo | None:
        result = await self.db.execute(
            select(AccountInfo).where(AccountInfo.id == account_id)
        )
        return result.scalars().first()

    async def add_account(self, account: AccountInfo) -> AccountInfo:
        self.db.add(account)
        await self.db.commit()
        await self.db.refresh(account)
        return account


async def get_account_repository(
    db: AsyncSession = Depends(get_pg_session),
) -> AccountRepository:
    return AccountRepository(db)
