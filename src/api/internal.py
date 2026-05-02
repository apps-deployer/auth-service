import uuid

import jwt
from fastapi import APIRouter, Header, HTTPException

from src.repositories.installation import InstallationRepository
from src.schemas import InstallationStatusResponse, InstallationUpsertRequest

router = APIRouter(prefix="/internal/github", tags=["internal-github"])


def _deps():
    from src.main import session_factory, settings
    return session_factory, settings


def _require_service(authorization: str = Header(...)):
    _, settings = _deps()
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization format")
    token = authorization.removeprefix("Bearer ")
    try:
        claims = jwt.decode(token, settings.auth.jwt_secret, algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError as e:
        raise HTTPException(status_code=401, detail=str(e))
    if claims.get("typ") != "service" and not str(claims.get("sub", "")).startswith("service:"):
        raise HTTPException(status_code=403, detail="Service token required")


@router.put("/installations", status_code=204)
async def upsert_installation(body: InstallationUpsertRequest, authorization: str = Header(...)):
    _require_service(authorization)
    factory, _ = _deps()
    async with factory() as session:
        repo = InstallationRepository(session)
        await repo.upsert(
            installation_id=body.installation_id,
            github_account_id=body.github_account_id,
            github_account_login=body.github_account_login,
            sender_github_id=body.sender_github_id,
        )
        await session.commit()


@router.delete("/installations/{installation_id}", status_code=204)
async def delete_installation(installation_id: int, authorization: str = Header(...)):
    _require_service(authorization)
    factory, _ = _deps()
    async with factory() as session:
        repo = InstallationRepository(session)
        await repo.delete_by_github_installation_id(installation_id)
        await session.commit()


@router.get("/installations/{installation_id}/exists")
async def installation_exists(installation_id: int, authorization: str = Header(...)):
    _require_service(authorization)
    factory, _ = _deps()
    async with factory() as session:
        repo = InstallationRepository(session)
        return {"exists": await repo.exists_by_github_installation_id(installation_id)}


@router.get("/installations/status", response_model=InstallationStatusResponse)
async def installation_status(
    authorization: str = Header(...),
    x_user_id: str = Header(..., alias="X-User-Id"),
):
    _require_service(authorization)
    factory, settings = _deps()
    async with factory() as session:
        repo = InstallationRepository(session)
        installed = await repo.user_has_installations(uuid.UUID(x_user_id))
        return InstallationStatusResponse(
            installed=installed,
            install_url=settings.github.app_install_url,
        )
