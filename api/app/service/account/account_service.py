from typing import Any

from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.component.database.postgres_client import get_pg_session
from app.entity.oauth.account_info import AccountInfo


class AccountService:

    def __init__(self, db: AsyncSession):
        self.db = db

    async def account_exists(self, openid: int) -> Any | None:
        result = await self.db.execute(select(AccountInfo).filter(AccountInfo.id == openid))
        return result.scalars().first()

    async def get_account_info(self, openid: int) -> AccountInfo | None:
        """
           根据 openid 获取完整的用户信息
           """
        result = await self.db.execute(
            select(AccountInfo).filter(AccountInfo.id == openid)
        )
        # 返回完整的 AccountInfo 对象，如果不存在则返回 None
        return result.scalars().first()

    async def create_account(self, account: AccountInfo):
        self.db.add(account)
        await self.db.commit()
        await self.db.refresh(account)


async def get_account_service(db: AsyncSession = Depends(get_pg_session)) -> AccountService:
    return AccountService(db)