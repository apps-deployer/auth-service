import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import User


class UserRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_github_id(self, github_id: int) -> User | None:
        stmt = select(User).where(User.github_id == github_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_id(self, user_id: uuid.UUID) -> User | None:
        return await self.session.get(User, user_id)

    async def create(
        self,
        github_id: int,
        github_login: str,
        avatar_url: str | None,
    ) -> User:
        user = User(
            github_id=github_id,
            github_login=github_login,
            avatar_url=avatar_url,
        )
        self.session.add(user)
        await self.session.flush()
        return user

    async def update(
        self,
        user: User,
        github_login: str,
        avatar_url: str | None,
    ) -> User:
        user.github_login = github_login
        user.avatar_url = avatar_url
        await self.session.flush()
        return user
