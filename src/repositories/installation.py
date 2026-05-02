import uuid

from sqlalchemy import delete, exists, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import Installation, InstallationUser, User


class InstallationRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_github_installation_id(self, installation_id: int) -> Installation | None:
        stmt = select(Installation).where(Installation.installation_id == installation_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def exists_by_github_installation_id(self, installation_id: int) -> bool:
        stmt = select(exists().where(Installation.installation_id == installation_id))
        result = await self.session.execute(stmt)
        return bool(result.scalar_one())

    async def user_has_installations(self, user_id: uuid.UUID) -> bool:
        stmt = select(exists().where(InstallationUser.user_id == user_id))
        result = await self.session.execute(stmt)
        return bool(result.scalar_one())

    async def upsert(
        self,
        installation_id: int,
        github_account_id: int,
        github_account_login: str,
        sender_github_id: int | None = None,
    ) -> Installation:
        installation = await self.get_by_github_installation_id(installation_id)
        if installation is None:
            installation = Installation(
                installation_id=installation_id,
                github_account_id=github_account_id,
                github_account_login=github_account_login,
            )
            self.session.add(installation)
            await self.session.flush()
        else:
            installation.github_account_id = github_account_id
            installation.github_account_login = github_account_login
            await self.session.flush()

        if sender_github_id is not None:
            user = await self._get_user_by_github_id(sender_github_id)
            if user is not None:
                await self._link_user(installation.id, user.id)

        return installation

    async def delete_by_github_installation_id(self, installation_id: int) -> bool:
        installation = await self.get_by_github_installation_id(installation_id)
        if installation is None:
            return False
        await self.session.delete(installation)
        await self.session.flush()
        return True

    async def _get_user_by_github_id(self, github_id: int) -> User | None:
        stmt = select(User).where(User.github_id == github_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def _link_user(self, installation_id: uuid.UUID, user_id: uuid.UUID) -> None:
        stmt = select(InstallationUser).where(
            InstallationUser.installation_id == installation_id,
            InstallationUser.user_id == user_id,
        )
        result = await self.session.execute(stmt)
        if result.scalar_one_or_none() is not None:
            return
        self.session.add(InstallationUser(installation_id=installation_id, user_id=user_id))
        await self.session.flush()
