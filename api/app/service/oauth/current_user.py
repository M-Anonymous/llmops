import os

import jwt
from fastapi import Cookie, HTTPException, Depends
from app.service.account.account_service import AccountService,get_account_service


class CurrentUser:

    async def __call__(self, token: str | None = Cookie(default=None), account_service: AccountService = Depends(get_account_service)) -> int:
        if not token:
            raise HTTPException(status_code=401, detail="未提供有效的凭证")

        try:
            jwt_secret = os.getenv("JWT_SECRET")
            # 2. 解析并验证 JWT Token
            payload = jwt.decode(token, jwt_secret, algorithms=["HS256"])
            account_id = int(payload.get("sub"))

            if account_id is None:
                raise HTTPException(status_code=401, detail="无效的 Token 载荷")

            # 3. 根据解析出的 ID 查询数据库，获取完整的用户对象
            current_user = await account_service.get_account_info(account_id)
            if not current_user:
                raise HTTPException(status_code=401, detail="用户不存在或已被禁用")
            # 4. 返回完整的用户对象
            return current_user.id
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Token 已过期")
        except jwt.PyJWTError:
            raise HTTPException(status_code=401, detail="Token 验证失败")


