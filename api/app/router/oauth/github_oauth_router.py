from fastapi import APIRouter, Depends, Query

from app.service.oauth.github_oauth_service import GithubOauthService, get_github_oauth_service

oauth_router = APIRouter(prefix="/auth", tags=["github"])


@oauth_router.get("/authorization_url")
async def get_authorization_url(oauth_service : GithubOauthService = Depends(get_github_oauth_service)) -> str:
    return oauth_service.get_oauth_url()


@oauth_router.get("/authorize")
async def authorize(code: str = Query(...),oauth_service : GithubOauthService = Depends(get_github_oauth_service)):
    return await oauth_service.authorize(code)