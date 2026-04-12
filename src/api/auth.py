import secrets
from urllib.parse import urlencode

import jwt
from fastapi import APIRouter, Header, HTTPException, Query
from fastapi.responses import RedirectResponse

from src.schemas import TokenResponse, UserResponse
from src.services.auth import AuthService

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])

GITHUB_AUTHORIZE_URL = "https://github.com/login/oauth/authorize"

# In-memory state store: state_token → True. Cleared on use.
# Sufficient for a single-process server; use Redis for multi-instance.
_pending_states: set[str] = set()


def _get_deps():
    from src.main import session_factory, github_client, settings
    return session_factory, github_client, settings


@router.get("/login/github")
async def login_github():
    _, _, settings = _get_deps()
    state = secrets.token_urlsafe(32)
    _pending_states.add(state)
    params = urlencode({
        "client_id": settings.github.client_id,
        "scope": "read:user",
        "state": state,
    })
    return RedirectResponse(url=f"{GITHUB_AUTHORIZE_URL}?{params}")


@router.get("/callback/github")
async def callback_github(code: str = Query(...), state: str = Query(...)):
    if state not in _pending_states:
        raise HTTPException(status_code=400, detail="Invalid or expired OAuth state")
    _pending_states.discard(state)

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

    frontend_url = settings.server.frontend_url.rstrip("/")
    redirect_url = f"{frontend_url}/auth/callback?token={result.access_token}"
    return RedirectResponse(url=redirect_url, status_code=302)


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
