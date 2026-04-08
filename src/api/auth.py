from urllib.parse import urlencode

import jwt
from fastapi import APIRouter, Header, HTTPException, Query
from fastapi.responses import RedirectResponse

from src.schemas import TokenResponse, UserResponse
from src.services.auth import AuthService

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])

GITHUB_AUTHORIZE_URL = "https://github.com/login/oauth/authorize"


def _get_deps():
    from src.main import session_factory, github_client, settings
    return session_factory, github_client, settings


@router.get("/login/github")
async def login_github():
    _, _, settings = _get_deps()
    params = urlencode({
        "client_id": settings.github.client_id,
        "scope": "read:user",
    })
    return RedirectResponse(url=f"{GITHUB_AUTHORIZE_URL}?{params}")


@router.get("/callback/github", response_model=TokenResponse)
async def callback_github(code: str = Query(...)):
    factory, gh_client, settings = _get_deps()
    async with factory() as session:
        svc = AuthService(
            session=session,
            github_client=gh_client,
            jwt_secret=settings.auth.jwt_secret,
            token_ttl_minutes=settings.auth.token_ttl_minutes,
        )
        try:
            result = await svc.handle_github_callback(code)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        await session.commit()
        return result


@router.get("/me", response_model=UserResponse)
async def me(authorization: str = Header(...)):
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")

    token = authorization.removeprefix("Bearer ")
    factory, _, settings = _get_deps()

    async with factory() as session:
        svc = AuthService(
            session=session,
            github_client=None,
            jwt_secret=settings.auth.jwt_secret,
            token_ttl_minutes=settings.auth.token_ttl_minutes,
        )
        try:
            user = await svc.get_current_user(token)
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Token expired")
        except (jwt.InvalidTokenError, ValueError) as e:
            raise HTTPException(status_code=401, detail=str(e))
        return UserResponse.model_validate(user)
