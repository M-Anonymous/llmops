from fastapi import APIRouter, Depends, Query, Response

from app.service.account.account_service import AccountService, get_account_service
from app.service.oauth.current_user import OptionalCurrentUser
from app.service.oauth.github_oauth_service import GithubOauthService, get_github_oauth_service

oauth_router = APIRouter(prefix="/auth", tags=["github"])


@oauth_router.get("/authorization_url")
async def get_authorization_url(oauth_service: GithubOauthService = Depends(get_github_oauth_service)) -> str:
    return oauth_service.get_oauth_url()


@oauth_router.get("/me")
async def get_current_user(
    account_id: int | None = Depends(OptionalCurrentUser()),
    account_service: AccountService = Depends(get_account_service),
):
    """查询登录状态：未登录也返回 200，避免前端首页误判为接口失败。"""
    if account_id is None:
        return {
            "id": None,
            "authenticated": False,
            "nickname": None,
            "avatar": None,
        }

    account = await account_service.get_account_info(account_id)
    return {
        "id": account_id,
        "authenticated": True,
        "nickname": account.nickname if account else None,
        "avatar": account.avatar if account else None,
    }


@oauth_router.post("/logout")
async def logout(response: Response):
    """清除登录 Cookie。"""
    response.delete_cookie(
        key="token",
        httponly=True,
        samesite="lax",
    )
    return {"status": "success"}


@oauth_router.get("/authorize")
async def authorize(
    code: str = Query(...),
    oauth_service: GithubOauthService = Depends(get_github_oauth_service),
):
    return await oauth_service.authorize(code)
