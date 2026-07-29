import os

import jwt
from fastapi import Cookie, Depends, HTTPException

from app.service.account.account_service import AccountService, get_account_service


class OptionalCurrentUser:
    """登录则返回 account_id；未登录或凭证无效返回 None（不抛 401）。"""

    async def __call__(
        self,
        token: str | None = Cookie(default=None),
        account_service: AccountService = Depends(get_account_service),
    ) -> int | None:
        if not token:
            return None

        try:
            jwt_secret = os.getenv("JWT_SECRET")
            if not jwt_secret:
                return None

            payload = jwt.decode(token, jwt_secret, algorithms=["HS256"])
            account_id = payload.get("sub")
            if account_id is None:
                return None

            current_user = await account_service.get_account_info(int(account_id))
            if not current_user:
                return None
            return current_user.id
        except (jwt.PyJWTError, ValueError, TypeError):
            return None


class CurrentUser:

    async def __call__(
        self,
        token: str | None = Cookie(default=None),
        account_service: AccountService = Depends(get_account_service),
    ) -> int:
        account_id = await OptionalCurrentUser()(token, account_service)
        if account_id is None:
            raise HTTPException(status_code=401, detail="未提供有效的凭证")
        return account_id
