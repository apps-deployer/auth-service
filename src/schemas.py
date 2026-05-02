import uuid
from datetime import datetime

from pydantic import BaseModel


class UserResponse(BaseModel):
    id: uuid.UUID
    github_login: str
    avatar_url: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class InstallationUpsertRequest(BaseModel):
    installation_id: int
    github_account_id: int
    github_account_login: str
    sender_github_id: int | None = None


class InstallationStatusResponse(BaseModel):
    installed: bool
    install_url: str
