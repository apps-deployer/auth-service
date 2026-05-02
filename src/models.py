import uuid
from datetime import datetime

from sqlalchemy import BigInteger, ForeignKey, text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"
    __table_args__ = {"schema": "auth"}

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, server_default=text("uuidv7()"))
    github_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False)
    github_login: Mapped[str] = mapped_column(nullable=False)
    avatar_url: Mapped[str | None]
    created_at: Mapped[datetime] = mapped_column(server_default=text("now()"))
    updated_at: Mapped[datetime] = mapped_column(server_default=text("now()"))


class Installation(Base):
    __tablename__ = "installations"
    __table_args__ = {"schema": "auth"}

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, server_default=text("uuidv7()"))
    installation_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False)
    github_account_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    github_account_login: Mapped[str] = mapped_column(nullable=False)
    created_at: Mapped[datetime] = mapped_column(server_default=text("now()"))

    users: Mapped[list["InstallationUser"]] = relationship(
        back_populates="installation",
        cascade="all, delete-orphan",
    )


class InstallationUser(Base):
    __tablename__ = "installation_users"
    __table_args__ = {"schema": "auth"}

    installation_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("auth.installations.id", ondelete="CASCADE"),
        primary_key=True,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("auth.users.id", ondelete="CASCADE"),
        primary_key=True,
    )
    created_at: Mapped[datetime] = mapped_column(server_default=text("now()"))

    installation: Mapped[Installation] = relationship(back_populates="users")
