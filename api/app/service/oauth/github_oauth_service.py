import os
import urllib.parse
from datetime import datetime, timezone, timedelta

import jwt
import requests
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import RedirectResponse

from app.component.database.postgres_client import get_pg_session
from app.dto.oauth.auth_user_info import AuthUserInfo
from app.entity.oauth.account_info import AccountInfo
from app.service import AccountService



class GithubOauthService:

    """GithubOAuth第三方授权认证类"""

    _AUTHORIZE_URL = "https://github.com/login/oauth/authorize"  # 跳转授权接口
    _ACCESS_TOKEN_URL = "https://github.com/login/oauth/access_token"  # 获取授权令牌接口
    _USER_INFO_URL = "https://api.github.com/user"  # 获取用户信息接口
    _EMAIL_INFO_URL = "https://api.github.com/user/emails"  # 获取用户邮箱接口

    def __init__(self,account_service: AccountService):

        self.client_id = os.getenv("GITHUB_CLIENT_ID")
        self.client_secret = os.getenv("GITHUB_CLIENT_SECRET")
        self.redirect_uri = os.getenv("GITHUB_REDIRECT_URI")
        self.account_service = account_service
        self.jwt_secret = os.getenv("JWT_SECRET")

    def get_oauth_url(self) -> str:
        params = {
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "scope": "user:email",  # 只请求用户的基本信息
        }
        return f"{self._AUTHORIZE_URL}?{urllib.parse.urlencode(params)}"

    def get_access_token(self, code: str) -> str:
        # 1.组装请求数据
        data = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "code": code,
            "redirect_uri": self.redirect_uri,
        }
        headers = {"Accept": "application/json"}

        # 2.发起post请求并获取相应的数据
        resp = requests.post(self._ACCESS_TOKEN_URL, data=data, headers=headers)
        resp.raise_for_status()
        resp_json = resp.json()

        # 3.提取access_token对应的数据
        access_token = resp_json.get("access_token")
        if not access_token:
            raise ValueError(f"Github OAuth授权失败: {resp_json}")

        return access_token

    def get_auth_user_info(self, access_token: str) -> AuthUserInfo:
        # 1.组装请求数据
        headers = {"Authorization": f"token {access_token}"}

        # 2.发起get请求获取用户数据
        resp = requests.get(self._USER_INFO_URL, headers=headers)
        resp.raise_for_status()
        raw_info = resp.json()

        # 3.发起get请求获取用户邮箱
        email_resp = requests.get(self._EMAIL_INFO_URL, headers=headers)
        email_resp.raise_for_status()
        email_info = email_resp.json()

        # 4.提取邮箱数据
        primary_email = next((email for email in email_info if email.get("primary", None)), None)

        return AuthUserInfo(
            id=raw_info.get("id"),
            name=raw_info.get("login"),
            avatar=raw_info.get("avatar_url"),
            email=primary_email.get("email"),
        )

    async def authorize(self, code: str) -> RedirectResponse:
        access_token = self.get_access_token(code)
        oauth_user_info = self.get_auth_user_info(access_token)
        openid = oauth_user_info.id
        if openid is None:
            raise ValueError("Account info missing 'id'")
        exist = await self.account_service.account_exists(openid)
        if not exist:
            account = AccountInfo(
                id=openid,  # 单独将 openid 转为 int
                email=oauth_user_info.email,
                nickname=oauth_user_info.name,
                avatar=oauth_user_info.avatar
            )
            await self.account_service.create_account(account)

        # 4. 生成业务 Token（这里以 JWT 为例，你也可以用 UUID 等）
        payload = {
            "sub": str(openid),
            "exp": datetime.now(timezone.utc) + timedelta(days=7)
        }
        # 注意：请替换为你项目中的真实 SECRET_KEY
        token = jwt.encode(payload, self.jwt_secret, algorithm="HS256")

        # 5. 创建重定向响应，并设置 Cookie
        response = RedirectResponse(url="http://localhost:8888", status_code=303)
        response.set_cookie(
            key="token",  # Cookie 的名称
            value=token,  # Token 的值
            httponly=True,  # 防止 XSS 攻击（推荐开启）
            secure=False,  # 本地开发用 False，生产环境改为 True
            samesite="lax",  # 防止 CSRF 攻击
            max_age=7 * 24 * 60 * 60  # Cookie 有效期（秒）
        )
        return response


async def get_github_oauth_service(db: AsyncSession = Depends(get_pg_session)) -> GithubOauthService:
        # 假设 GithubOauthService 的初始化也需要 db session
        return GithubOauthService(AccountService(db))
