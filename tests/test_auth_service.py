import uuid
from datetime import datetime, UTC
from unittest.mock import AsyncMock, MagicMock, patch

import jwt as pyjwt
import pytest

from src.models import User
from src.schemas import TokenResponse
from src.services.auth import AuthService
from src.services.github import GitHubUser


SECRET = "test-secret"
TTL = 60


def make_user(**kwargs) -> User:
    defaults = dict(
        id=uuid.uuid4(),
        github_id=12345,
        github_login="testuser",
        avatar_url="https://avatars.githubusercontent.com/u/12345",
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    defaults.update(kwargs)
    user = MagicMock(spec=User)
    for k, v in defaults.items():
        setattr(user, k, v)
    return user


@pytest.fixture
def mock_session():
    return AsyncMock()


@pytest.fixture
def mock_github():
    client = AsyncMock()
    client.exchange_code = AsyncMock(return_value="gh-access-token")
    client.get_user_info = AsyncMock(return_value=GitHubUser(
        id=12345,
        login="testuser",
        avatar_url="https://avatars.githubusercontent.com/u/12345",
    ))
    return client


@pytest.mark.asyncio
async def test_handle_github_callback_new_user(mock_session, mock_github):
    svc = AuthService(
        session=mock_session,
        github_client=mock_github,
        jwt_secret=SECRET,
        token_ttl_minutes=TTL,
    )

    # Simulate new user (not found in DB)
    with patch.object(svc.repo, "get_by_github_id", new=AsyncMock(return_value=None)), \
         patch.object(svc.repo, "create", new=AsyncMock(return_value=make_user())):
        result = await svc.handle_github_callback("auth-code-123")

    assert isinstance(result, TokenResponse)
    assert result.token_type == "bearer"
    assert result.expires_in == TTL * 60

    # Verify JWT is valid
    claims = pyjwt.decode(result.access_token, SECRET, algorithms=["HS256"])
    assert claims["github_login"] == "testuser"


@pytest.mark.asyncio
async def test_handle_github_callback_existing_user(mock_session, mock_github):
    existing_user = make_user()
    svc = AuthService(
        session=mock_session,
        github_client=mock_github,
        jwt_secret=SECRET,
        token_ttl_minutes=TTL,
    )

    with patch.object(svc.repo, "get_by_github_id", new=AsyncMock(return_value=existing_user)), \
         patch.object(svc.repo, "update", new=AsyncMock(return_value=existing_user)):
        result = await svc.handle_github_callback("auth-code-123")

    assert isinstance(result, TokenResponse)
    claims = pyjwt.decode(result.access_token, SECRET, algorithms=["HS256"])
    assert claims["sub"] == str(existing_user.id)


@pytest.mark.asyncio
async def test_get_current_user_success(mock_session):
    user = make_user()
    token = pyjwt.encode({"sub": str(user.id)}, SECRET, algorithm="HS256")

    svc = AuthService(
        session=mock_session,
        github_client=None,
        jwt_secret=SECRET,
        token_ttl_minutes=TTL,
    )

    with patch.object(svc.repo, "get_by_id", new=AsyncMock(return_value=user)):
        result = await svc.get_current_user(token)

    assert result.id == user.id


@pytest.mark.asyncio
async def test_get_current_user_not_found(mock_session):
    user_id = uuid.uuid4()
    token = pyjwt.encode({"sub": str(user_id)}, SECRET, algorithm="HS256")

    svc = AuthService(
        session=mock_session,
        github_client=None,
        jwt_secret=SECRET,
        token_ttl_minutes=TTL,
    )

    with patch.object(svc.repo, "get_by_id", new=AsyncMock(return_value=None)):
        with pytest.raises(ValueError, match="User not found"):
            await svc.get_current_user(token)
