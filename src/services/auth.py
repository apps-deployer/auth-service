import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from src.jwt import decode_token, encode_token
from src.models import User
from src.repositories.user import UserRepository
from src.schemas import TokenResponse
from src.services.github import GitHubOAuthClient


class AuthService:
    def __init__(
        self,
        session: AsyncSession,
        github_client: GitHubOAuthClient,
        jwt_secret: str,
        token_ttl_minutes: int,
    ):
        self.repo = UserRepository(session)
        self.github_client = github_client
        self.jwt_secret = jwt_secret
        self.token_ttl_minutes = token_ttl_minutes

    async def handle_github_callback(self, code: str) -> TokenResponse:
        access_token = await self.github_client.exchange_code(code)
        gh_user = await self.github_client.get_user_info(access_token)

        user = await self.repo.get_by_github_id(gh_user.id)
        if user is None:
            user = await self.repo.create(
                github_id=gh_user.id,
                github_login=gh_user.login,
                avatar_url=gh_user.avatar_url,
            )
        else:
            user = await self.repo.update(
                user=user,
                github_login=gh_user.login,
                avatar_url=gh_user.avatar_url,
            )

        token = encode_token(
            user_id=str(user.id),
            github_login=user.github_login,
            secret=self.jwt_secret,
            ttl_minutes=self.token_ttl_minutes,
        )

        return TokenResponse(
            access_token=token,
            expires_in=self.token_ttl_minutes * 60,
        )

    async def get_current_user(self, token: str) -> User:
        claims = decode_token(token, self.jwt_secret)
        user = await self.repo.get_by_id(uuid.UUID(claims["sub"]))
        if user is None:
            raise ValueError("User not found")
        return user
