from fastapi import Depends

from app.entity.oauth.account_info import AccountInfo
from app.repository.account.account_repository import (
    AccountRepository,
    get_account_repository,
)


class AccountService:

    def __init__(self, account_repository: AccountRepository):
        self.account_repository = account_repository

    async def account_exists(self, openid: int) -> AccountInfo | None:
        return await self.account_repository.find_by_id(openid)

    async def get_account_info(self, openid: int) -> AccountInfo | None:
        return await self.account_repository.find_by_id(openid)

    async def create_account(self, account: AccountInfo) -> AccountInfo:
        return await self.account_repository.add_account(account)


async def get_account_service(
    account_repository: AccountRepository = Depends(get_account_repository),
) -> AccountService:
    return AccountService(account_repository)
